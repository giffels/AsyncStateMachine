from kubernetes_asyncio import client as k8s_client
from kubernetes_asyncio import client as hpa_client
from kubernetes_asyncio.client.rest import ApiException as K8SApiException
from ...exceptions.tardisexceptions import TardisError
from ...interfaces.siteadapter import SiteAdapter
from ...interfaces.siteadapter import ResourceStatus
from ...utilities.attributedict import AttributeDict
from ...utilities.staticmapping import StaticMapping

from functools import partial
from datetime import datetime
from contextlib import contextmanager


class KubernetesAdapter(SiteAdapter):
    def __init__(self, machine_type: str, site_name: str):
        self._machine_type = machine_type
        self._site_name = site_name
        key_translator = StaticMapping(
            remote_resource_uuid="uid", drone_uuid="name", resource_status="type"
        )
        translator_functions = StaticMapping(
            created=lambda date: datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z"),
            updated=lambda date: datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z"),
            type=lambda x, translator=StaticMapping(
                Booting=ResourceStatus.Booting,
                Progressing=ResourceStatus.Running,
                Available=ResourceStatus.Running,
                Stopped=ResourceStatus.Stopped,
                Deleted=ResourceStatus.Deleted,
                ReplicaFailure=ResourceStatus.Error,
            ): translator[x],
        )
        self.handle_response = partial(
            self.handle_response,
            key_translator=key_translator,
            translator_functions=translator_functions,
        )
        self._client = None
        self._hpa_client = None

    @property
    def client(self) -> k8s_client.AppsV1Api:
        if self._client is None:
            a_configuration = k8s_client.Configuration(
                host=self.configuration.host,
                api_key={"authorization": self.configuration.token},
            )
            a_configuration.api_key_prefix["authorization"] = "Bearer"
            a_configuration.verify_ssl = False
            self._client = k8s_client.AppsV1Api(k8s_client.ApiClient(a_configuration))
        return self._client

    @property
    def hpa_client(self) -> hpa_client.AutoscalingV1Api:
        if self._hpa_client is None:
            a_configuration = hpa_client.Configuration(
                host=self.configuration.host,
                api_key={"authorization": self.configuration.token},
            )
            a_configuration.api_key_prefix["authorization"] = "Bearer"
            a_configuration.verify_ssl = False
            self._hpa_client = hpa_client.AutoscalingV1Api(
                hpa_client.ApiClient(a_configuration)
            )
        return self._hpa_client

    async def deploy_resource(
        self, resource_attributes: AttributeDict
    ) -> AttributeDict:
        spec = k8s_client.V1DeploymentSpec(
            replicas=1,
            selector=k8s_client.V1LabelSelector(
                match_labels={"app": resource_attributes.drone_uuid}
            ),
            template=k8s_client.V1PodTemplateSpec(),
        )
        spec.template.metadata = k8s_client.V1ObjectMeta(
            name=resource_attributes.drone_uuid,
            labels={"app": resource_attributes.drone_uuid},
        )
        container = k8s_client.V1Container(
            image=self.machine_type_configuration.image,
            args=self.machine_type_configuration.args,
            name=resource_attributes.drone_uuid,
            resources=k8s_client.V1ResourceRequirements(
                requests={
                    "cpu": self.machine_meta_data.Cores,
                    "memory": self.machine_meta_data.Memory,
                }
            ),
        )
        spec.template.spec = k8s_client.V1PodSpec(containers=[container])
        body = k8s_client.V1Deployment(
            metadata=k8s_client.V1ObjectMeta(name=resource_attributes.drone_uuid),
            spec=spec,
        )
        response_temp = await self.client.create_namespaced_deployment(
            namespace=self.machine_type_configuration.namespace, body=body
        )
        response = {
            "uid": response_temp.metadata.uid,
            "name": response_temp.metadata.name,
            "type": "Booting",
        }
        if self.machine_type_configuration.hpa:
            spec = hpa_client.V1HorizontalPodAutoscalerSpec(
                max_replicas=self.machine_type_configuration.max_replicas,
                min_replicas=self.machine_type_configuration.min_replicas,
                target_cpu_utilization_percentage=self.machine_type_configuration.cpu_utilization,  # noqa: B950
                scale_target_ref=hpa_client.V1CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=resource_attributes.drone_uuid,
                ),
            )
            dep = hpa_client.V1HorizontalPodAutoscaler(
                metadata=hpa_client.V1ObjectMeta(name=resource_attributes.drone_uuid),
                spec=spec,
            )
            await self.hpa_client.create_namespaced_horizontal_pod_autoscaler(
                namespace=self.machine_type_configuration.namespace, body=dep
            )
        return self.handle_response(response)

    async def resource_status(
        self, resource_attributes: AttributeDict
    ) -> AttributeDict:
        try:
            response_temp = await self.client.read_namespaced_deployment(
                name=resource_attributes.drone_uuid,
                namespace=self.machine_type_configuration.namespace,
            )
            response_uid = response_temp.metadata.uid
            response_name = response_temp.metadata.name
            if response_temp.spec.replicas == 0:
                response_type = "Stopped"
            else:
                if response_temp.status.available_replicas is None:
                    response_type = "Booting"
                else:
                    response_type = response_temp.status.conditions[0].type
        except K8SApiException as ex:
            if ex.status != 404:
                raise
            response_uid = resource_attributes.remote_resource_uuid
            response_name = resource_attributes.drone_uuid
            response_type = "Deleted"
        response = {"uid": response_uid, "name": response_name, "type": response_type}
        return self.handle_response(response)

    async def stop_resource(self, resource_attributes: AttributeDict):
        body = await self.client.read_namespaced_deployment(
            name=resource_attributes.drone_uuid,
            namespace=self.machine_type_configuration.namespace,
        )
        body.spec.replicas = 0
        response = await self.client.replace_namespaced_deployment(
            name=resource_attributes.drone_uuid,
            namespace=self.machine_type_configuration.namespace,
            body=body,
        )
        return response

    async def terminate_resource(self, resource_attributes: AttributeDict):
        response = None
        try:
            response = await self.client.delete_namespaced_deployment(
                name=resource_attributes.drone_uuid,
                namespace=self.machine_type_configuration.namespace,
                body=k8s_client.V1DeleteOptions(
                    propagation_policy="Foreground", grace_period_seconds=5
                ),
            )
        except K8SApiException as ex:
            if ex.status != 404:
                raise
        if self.machine_type_configuration.hpa:
            try:
                await self.hpa_client.delete_namespaced_horizontal_pod_autoscaler(
                    name=resource_attributes.drone_uuid,
                    namespace=self.machine_type_configuration.namespace,
                )
            except K8SApiException as ex:
                if ex.status != 404:
                    raise
        return response

    @contextmanager
    def handle_exceptions(self):
        try:
            yield
        except Exception as ex:
            raise TardisError from ex

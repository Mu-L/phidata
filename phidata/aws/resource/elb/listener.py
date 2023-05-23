from typing import Optional, Any, Dict, List

from phidata.aws.api_client import AwsApiClient
from phidata.aws.resource.base import AwsResource
from phidata.aws.resource.elb.load_balancer import LoadBalancer
from phidata.aws.resource.elb.target_group import TargetGroup
from phidata.utils.cli_console import print_info, print_error, print_warning
from phidata.utils.log import logger


class Listener(AwsResource):
    """
    https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/elbv2/client/create_listener.html
    """

    resource_type = "Listener"
    service_name = "elbv2"

    # Name of the Listener
    name: str
    load_balancer: Optional[LoadBalancer] = None
    target_group: Optional[TargetGroup] = None
    load_balancer_arn: Optional[str] = None
    protocol: Optional[str] = None
    port: Optional[int] = None
    ssl_policy: Optional[str] = None
    certificates: Optional[List[Dict[str, Any]]]
    default_actions: Optional[List[Dict]]
    alpn_policy: Optional[List[str]]
    tags: Optional[List[Dict[str, str]]]

    def _create(self, aws_client: AwsApiClient) -> bool:
        """Creates the Listener

        Args:
            aws_client: The AwsApiClient for the current Listener
        """
        print_info(f"Creating {self.get_resource_type()}: {self.get_resource_name()}")

        load_balancer_arn = self.get_load_balancer_arn(aws_client)
        if load_balancer_arn is None:
            logger.error(f"Load balancer ARN not available")
            return True

        # create a dict of args which are not null, otherwise aws type validation fails
        not_null_args: Dict[str, Any] = {}
        if self.protocol is not None:
            not_null_args["Protocol"] = self.protocol
        if self.port is not None:
            not_null_args["Port"] = self.port
        if self.ssl_policy is not None:
            not_null_args["SslPolicy"] = self.ssl_policy
        if self.certificates is not None:
            not_null_args["Certificates"] = self.certificates
        if self.alpn_policy is not None:
            not_null_args["AlpnPolicy"] = self.alpn_policy
        if self.tags is not None:
            not_null_args["Tags"] = self.tags

        if self.default_actions is not None:
            not_null_args["DefaultActions"] = self.default_actions
        elif self.target_group is not None:
            target_group_arn = self.target_group.get_arn(aws_client)
            if target_group_arn is None:
                logger.error(f"Target group ARN not available")
                return False
            not_null_args["DefaultActions"] = [
                {"Type": "forward", "TargetGroupArn": target_group_arn}
            ]
        else:
            print_warning(
                f"Neither target group nor default actions provided for {self.get_resource_name()}"
            )
            return True

        # Create Listener
        service_client = self.get_service_client(aws_client)
        try:
            create_response = service_client.create_listener(
                LoadBalancerArn=load_balancer_arn,
                **not_null_args,
            )
            logger.debug(f"Create Response: {create_response}")
            resource_dict = create_response.get("Listeners", {})

            # Validate resource creation
            if resource_dict is not None:
                print_info(f"Listener created: {self.get_resource_name()}")
                self.active_resource = create_response
                return True
        except Exception as e:
            print_error(f"{self.get_resource_type()} could not be created.")
            print_error(e)
        return False

    def _read(self, aws_client: AwsApiClient) -> Optional[Any]:
        """Returns the Listener

        Args:
            aws_client: The AwsApiClient for the current Listener
        """
        logger.debug(f"Reading {self.get_resource_type()}: {self.get_resource_name()}")

        from botocore.exceptions import ClientError

        service_client = self.get_service_client(aws_client)
        try:
            load_balancer_arn = self.get_load_balancer_arn(aws_client)
            if load_balancer_arn is None:
                # logger.error(f"Load balancer ARN not available")
                return None

            describe_response = service_client.describe_listeners(
                LoadBalancerArn=load_balancer_arn
            )
            logger.debug(f"Describe Response: {describe_response}")
            resource_list = describe_response.get("Listeners", None)

            if resource_list is not None and isinstance(resource_list, list):
                self.active_resource = (
                    resource_list[0] if len(resource_list) > 0 else None
                )
        except ClientError as ce:
            logger.debug(f"ClientError: {ce}")
        except Exception as e:
            print_error(f"Error reading {self.get_resource_type()}.")
            print_error(e)
        return self.active_resource

    def _delete(self, aws_client: AwsApiClient) -> bool:
        """Deletes the Listener

        Args:
            aws_client: The AwsApiClient for the current Listener
        """
        print_info(f"Deleting {self.get_resource_type()}: {self.get_resource_name()}")

        service_client = self.get_service_client(aws_client)
        self.active_resource = None

        try:
            listener_arn = self.get_arn(aws_client)
            if listener_arn is None:
                print_error(f"Listener {self.get_resource_name()} not found.")
                return True

            delete_response = service_client.delete_listener(ListenerArn=listener_arn)
            logger.debug(f"Delete Response: {delete_response}")
            print_info(
                f"{self.get_resource_type()}: {self.get_resource_name()} deleted"
            )
            return True
        except Exception as e:
            print_error(f"{self.get_resource_type()} could not be deleted.")
            print_error("Please try again or delete resources manually.")
            print_error(e)
        return False

    def _update(self, aws_client: AwsApiClient) -> bool:
        """Update EcsService"""
        print_info(f"Updating {self.get_resource_type()}: {self.get_resource_name()}")

        listener_arn = self.get_arn
        if listener_arn is None:
            print_error(f"Listener {self.get_resource_name()} not found.")
            return True

        # create a dict of args which are not null, otherwise aws type validation fails
        not_null_args: Dict[str, Any] = {}
        if self.protocol is not None:
            not_null_args["Protocol"] = self.protocol
        if self.port is not None:
            not_null_args["Port"] = self.port
        if self.ssl_policy is not None:
            not_null_args["SslPolicy"] = self.ssl_policy
        if self.certificates is not None:
            not_null_args["Certificates"] = self.certificates
        if self.default_actions is not None:
            not_null_args["DefaultActions"] = self.default_actions
        if self.alpn_policy is not None:
            not_null_args["AlpnPolicy"] = self.alpn_policy

        service_client = self.get_service_client(aws_client)
        try:
            create_response = service_client.modify_listener(
                ListenerArn=listener_arn,
                **not_null_args,
            )
            logger.debug(f"Update Response: {create_response}")
            resource_dict = create_response.get("Listeners", {})

            # Validate resource creation
            if resource_dict is not None:
                print_info(f"Listener updated: {self.get_resource_name()}")
                self.active_resource = create_response
                return True
        except Exception as e:
            print_error(f"{self.get_resource_type()} could not be created.")
            print_error(e)
        return False

    def get_arn(self, aws_client: AwsApiClient) -> Optional[str]:
        listener = self._read(aws_client)
        if listener is None:
            return None

        listener_arn = listener.get("ListenerArn", None)
        return listener_arn

    def get_load_balancer_arn(self, aws_client: AwsApiClient):
        load_balancer_arn = self.load_balancer_arn
        if load_balancer_arn is None and self.load_balancer:
            load_balancer_arn = self.load_balancer.get_arn(aws_client)

        return load_balancer_arn
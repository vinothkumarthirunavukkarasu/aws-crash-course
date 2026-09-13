import os

from aws_cdk import (
    CfnOutput,
    Duration,
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_events as events,
    aws_events_targets as targets,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)

from aws_cdk.aws_apigatewayv2_integrations import (
    HttpEventBridgeIntegration,
)

from constructs import Construct


class InfrastructureStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs
    ) -> None:

        super().__init__(scope, construct_id, **kwargs)

        #
        # 1. Lambda
        #

        validator = lambda_.Function(
            self,
            "ValidatorFunction",
            function_name="project-x-cdk-validator",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "..",
                    "lambda",
                    "validator",
                )
            ),
            timeout=Duration.seconds(30),
        )

        #
        # 2. Step Functions
        #

        validation_failed = sfn.Fail(
            self,
            "ValidationFailed",
            error="ValidationError",
            cause="Request validation failed",
        )

        validate_request = tasks.LambdaInvoke(
            self,
            "ValidateRequest",
            lambda_function=validator,
            payload=sfn.TaskInput.from_json_path_at("$"),
            output_path="$.Payload",
        )

        validate_request.add_catch(
            validation_failed,
            result_path="$.error",
        )

        workflow = sfn.StateMachine(
            self,
            "ProjectXWorkflow",
            state_machine_name="project-x-cdk-workflow",
            definition_body=sfn.DefinitionBody.from_chainable(
                validate_request
            ),
            timeout=Duration.minutes(5),
        )

        #
        # 3. EventBridge custom bus
        #

        event_bus = events.EventBus(
            self,
            "ProjectXEventBus",
            event_bus_name="project-x-cdk-bus",
        )

        #
        # 4. EventBridge rule
        #

        request_rule = events.Rule(
            self,
            "RequestReceivedRule",
            rule_name="project-x-cdk-request-received-rule",
            event_bus=event_bus,
            event_pattern=events.EventPattern(
                source=["projectx.requests"],
                detail_type=["RequestReceived"],
            ),
        )

        request_rule.add_target(
            targets.SfnStateMachine(
                workflow,
                input=events.RuleTargetInput.from_event_path(
                    "$.detail"
                ),
            )
        )

        #
        # 5. API Gateway HTTP API
        #

        http_api = apigwv2.HttpApi(
            self,
            "ProjectXHttpApi",
            api_name="project-x-cdk-api",
            description="Project X CDK POC API",
        )

        #
        # API Gateway -> EventBridge integration
        #

        parameter_mapping = (
            apigwv2.ParameterMapping()
            .custom("Detail", "$request.body")
            .custom("DetailType", "RequestReceived")
            .custom("Source", "projectx.requests")
        )

        eventbridge_integration = HttpEventBridgeIntegration(
            "ProjectXEventBridgeIntegration",
            event_bus_ref=event_bus.event_bus_ref,
            parameter_mapping=parameter_mapping,
        )

        http_api.add_routes(
            path="/requests",
            methods=[apigwv2.HttpMethod.POST],
            integration=eventbridge_integration,
        )

        #
        # 6. Outputs
        #

        CfnOutput(
            self,
            "ApiEndpoint",
            value=http_api.api_endpoint,
        )

        CfnOutput(
            self,
            "EventBusName",
            value=event_bus.event_bus_name,
        )

        CfnOutput(
            self,
            "WorkflowArn",
            value=workflow.state_machine_arn,
        )
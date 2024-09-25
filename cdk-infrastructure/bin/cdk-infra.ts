#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { InfrastructureStack } from "../lib/infrastructure-stack";
import { RepositoryStack } from "../lib/repository-stack";

const app = new cdk.App();

new RepositoryStack(app, "ECRRepositoryStack", {});
new InfrastructureStack(app, "InfrastructureStack", {});

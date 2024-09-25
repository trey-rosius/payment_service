export class ServiceApiToken {
  service: string;
  apiToken: string;
  http_url: string;
  grpc_url: string;
  strype_key: string;

  constructor(
    service: string,
    apiToken: string,
    grpc_url: string,
    http_url: string,
    stripe_key: string
  ) {
    this.service = service;
    this.apiToken = apiToken;
    this.grpc_url = grpc_url;
    this.http_url = http_url;
    this.stripe_key = stripe_key;
  }
}

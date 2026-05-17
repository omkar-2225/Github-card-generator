# Cloud Run Deployment Summary

The `github-card-generator` project has been successfully deployed to Google Cloud Run!

## Services Deployed

### Frontend
- **URL**: [https://github-card-frontend-15131588805.us-central1.run.app](https://github-card-frontend-15131588805.us-central1.run.app)
- **Configuration**: Port `80`, publicly accessible.
- **Environment**: Linked to the Backend URL.

### Backend
- **URL**: [https://github-card-backend-15131588805.us-central1.run.app](https://github-card-backend-15131588805.us-central1.run.app)
- **Configuration**: Port `8080`, publicly accessible.

> [!TIP]
> You can visit the **Frontend URL** in your browser to interact with the application.

## Troubleshooting Notes

During the deployment, we encountered a couple of minor issues which were successfully resolved:
1. **Billing Error**: Cloud Run requires an active billing account. We resolved this by linking your existing Trial Billing Account to the project.
2. **Port Configuration**: The frontend container uses Nginx, which listens on port `80` by default. We updated the Cloud Run configuration to explicitly expect traffic on port `80` instead of the default `8080`.

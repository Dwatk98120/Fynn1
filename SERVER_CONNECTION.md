# First Sound Helper — Phone ↔ Server Connection

## Recommended architecture

Android phone → HTTPS → FastAPI server → phoneme model → JSON response → Android app

The app supports three practical environments:

### 1. Android emulator
Use the default:
`http://10.0.2.2:8787`

`10.0.2.2` maps from the Android emulator to the computer running FastAPI.

### 2. Physical Android phone during development
Put the phone and development computer on the same Wi-Fi network.

Find the computer's LAN IP, for example:
`192.168.1.50`

Start FastAPI on all interfaces, for example:
`uvicorn app:app --host 0.0.0.0 --port 8787`

Then set:
`PARENT_PC_LOCAL_API_URL=http://192.168.1.50:8787`

Also allow TCP port 8787 through the computer's firewall for the private/local network.

### 3. Production / pilot
Use a public HTTPS endpoint, for example:
`https://api.example.com`

Do not use plain HTTP for production.

## Setting the URL

The Android build reads the Gradle property:

`PARENT_PC_LOCAL_API_URL`

For local development, add it to `gradle.properties` on the development machine, not to source control:

`PARENT_PC_LOCAL_API_URL=http://192.168.1.50:8787`

For production builds, supply the HTTPS URL as a Gradle property or CI build parameter.

## Privacy expectations

- Keep Offline Mode available.
- Do not commit recordings, student data, `local.properties`, keystores, or private credentials.
- Production API traffic should use HTTPS.
- The server should delete temporary uploaded audio after analysis unless the caregiver has explicitly enabled a storage workflow.
- Do not use student recordings for model training without separate authorization.


## Parent PC local backend production

The repository includes `Parent PC local backend.yaml` and a Parent PC local backend-ready Dockerfile.

Production Android builds should use:

`PARENT_PC_LOCAL_API_URL=[removed-cloud-backend]`

For a custom domain, replace that URL with your HTTPS API domain.

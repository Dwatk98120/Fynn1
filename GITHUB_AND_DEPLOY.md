# First Sound Helper — GitHub + deployment

## Put this project on GitHub
1. Create a new **private** repository named `first-sound-helper`.
2. Upload the contents of this folder to the repository.
3. Keep the repository private while developing and testing.

## Deploy the speech-analysis API
This project includes `Parent PC local backend.yaml` and `server/Dockerfile`.
In Parent PC local backend, create a new Blueprint from the GitHub repository.
Parent PC local backend should detect `Parent PC local backend.yaml` and deploy `first-sound-helper-api`.

After deployment, copy the HTTPS service URL.

## Build the Android app against the deployed API
In Android Studio, add this Gradle property when building:

`PARENT_PC_LOCAL_API_URL=[removed-cloud-backend]`

For the Android emulator, the default remains:
`http://10.0.2.2:8787`

For a real phone, use the HTTPS deployed URL.

## Important privacy settings for production
- Use HTTPS only.
- Add authentication before real-world use.
- Do not retain children's audio unless necessary and consented.
- Restrict CORS to the app/web origins you actually use.
- Do not use recordings for model training without separate authorization.


## Recording retention
Keep cloud audio retention disabled by default. Local recordings should be caregiver-controlled and deletable.

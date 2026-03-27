@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM ===== Required inputs (edit these) =====
set "PROJECT_ID=gen-lang-client-0567547134"
set "PROJECT_NUMBER=441535054378"
set "POOL_ID=github-actions-pool"
set "PROVIDER_ID=github-oidc"
set "GITHUB_ORG=your-org"
set "GITHUB_REPO=care_rag_api"
set "WIF_SA_EMAIL=ci-wif@%PROJECT_ID%.iam.gserviceaccount.com"
set "INVOKER_SA_EMAIL=441535054378-compute@developer.gserviceaccount.com"
set "CLOUD_RUN_SERVICE=care-rag-api-441535054378"
set "CLOUD_RUN_REGION=asia-east1"
set "CLOUD_RUN_URL=https://care-rag-api-441535054378.asia-east1.run.app"

set "ERR=0"

echo.
echo [0/6] Precheck gcloud
where gcloud >nul 2>nul
if errorlevel 1 (
  echo [FAIL] gcloud not found in PATH
  set /a ERR+=1
) else (
  echo [PASS] gcloud found
)

echo.
echo [1/6] APIs enabled (iam, iamcredentials, sts)
gcloud services list --enabled --project=%PROJECT_ID% --filter="name:(iam.googleapis.com OR iamcredentials.googleapis.com OR sts.googleapis.com)" > "%TEMP%\wif_services.txt" 2>&1
if errorlevel 1 (
  echo [FAIL] cannot query enabled services
  set /a ERR+=1
) else (
  findstr /c:"iam.googleapis.com" "%TEMP%\wif_services.txt" >nul || set /a ERR+=1
  findstr /c:"iamcredentials.googleapis.com" "%TEMP%\wif_services.txt" >nul || set /a ERR+=1
  findstr /c:"sts.googleapis.com" "%TEMP%\wif_services.txt" >nul || set /a ERR+=1
  if !errorlevel! equ 0 (
    echo [PASS] required APIs are enabled
  ) else (
    echo [FAIL] one or more required APIs are missing
  )
)

echo.
echo [2/6] Provider exists and issuer is GitHub OIDC
gcloud iam workload-identity-pools providers describe %PROVIDER_ID% --project=%PROJECT_ID% --location=global --workload-identity-pool=%POOL_ID% --format="yaml(oidc.issuerUri,attributeCondition)" > "%TEMP%\wif_provider.txt" 2>&1
if errorlevel 1 (
  echo [FAIL] provider not found or no permission
  set /a ERR+=1
) else (
  findstr /c:"https://token.actions.githubusercontent.com" "%TEMP%\wif_provider.txt" >nul
  if errorlevel 1 (
    echo [FAIL] issuerUri mismatch
    set /a ERR+=1
  ) else (
    echo [PASS] provider issuerUri is correct
  )
)

echo.
echo [3/6] WIF_SA has workloadIdentityUser for repo principalSet
set "EXPECTED_PRINCIPAL=principalSet://iam.googleapis.com/projects/%PROJECT_NUMBER%/locations/global/workloadIdentityPools/%POOL_ID%/attribute.repository/%GITHUB_ORG%/%GITHUB_REPO%"
gcloud iam service-accounts get-iam-policy %WIF_SA_EMAIL% --project=%PROJECT_ID% --format="yaml(bindings)" > "%TEMP%\wif_sa_policy.txt" 2>&1
if errorlevel 1 (
  echo [FAIL] cannot read WIF_SA IAM policy
  set /a ERR+=1
) else (
  findstr /c:"roles/iam.workloadIdentityUser" "%TEMP%\wif_sa_policy.txt" >nul
  if errorlevel 1 (
    echo [FAIL] missing roles/iam.workloadIdentityUser
    set /a ERR+=1
  ) else (
    findstr /c:"%EXPECTED_PRINCIPAL%" "%TEMP%\wif_sa_policy.txt" >nul
    if errorlevel 1 (
      echo [FAIL] expected principalSet not found
      set /a ERR+=1
    ) else (
      echo [PASS] workloadIdentityUser binding looks correct
    )
  )
)

echo.
echo [4/6] WIF_SA can impersonate INVOKER_SA (TokenCreator)
gcloud iam service-accounts get-iam-policy %INVOKER_SA_EMAIL% --project=%PROJECT_ID% --format="yaml(bindings)" > "%TEMP%\invoker_sa_policy.txt" 2>&1
if errorlevel 1 (
  echo [FAIL] cannot read INVOKER_SA IAM policy
  set /a ERR+=1
) else (
  findstr /c:"roles/iam.serviceAccountTokenCreator" "%TEMP%\invoker_sa_policy.txt" >nul
  if errorlevel 1 (
    echo [FAIL] missing roles/iam.serviceAccountTokenCreator
    set /a ERR+=1
  ) else (
    findstr /c:"serviceAccount:%WIF_SA_EMAIL%" "%TEMP%\invoker_sa_policy.txt" >nul
    if errorlevel 1 (
      echo [FAIL] WIF_SA not found in TokenCreator members
      set /a ERR+=1
    ) else (
      echo [PASS] TokenCreator binding looks correct
    )
  )
)

echo.
echo [5/6] INVOKER_SA has run.invoker on Cloud Run service
gcloud run services get-iam-policy %CLOUD_RUN_SERVICE% --project=%PROJECT_ID% --region=%CLOUD_RUN_REGION% --format="yaml(bindings)" > "%TEMP%\run_policy.txt" 2>&1
if errorlevel 1 (
  echo [FAIL] cannot read Cloud Run IAM policy
  set /a ERR+=1
) else (
  findstr /c:"roles/run.invoker" "%TEMP%\run_policy.txt" >nul
  if errorlevel 1 (
    echo [FAIL] missing roles/run.invoker
    set /a ERR+=1
  ) else (
    findstr /c:"serviceAccount:%INVOKER_SA_EMAIL%" "%TEMP%\run_policy.txt" >nul
    if errorlevel 1 (
      echo [FAIL] INVOKER_SA not found in run.invoker members
      set /a ERR+=1
    ) else (
      echo [PASS] Cloud Run invoker binding looks correct
    )
  )
)

echo.
echo [6/6] Audience sanity check
echo %CLOUD_RUN_URL% | findstr /b /c:"https://" >nul
if errorlevel 1 (
  echo [FAIL] CLOUD_RUN_URL must start with https://
  set /a ERR+=1
) else (
  echo [PASS] audience format starts with https://
)

echo.
if %ERR% EQU 0 (
  echo ==========================================
  echo READY: WIF double-SA baseline checks pass.
  echo ==========================================
  exit /b 0
) else (
  echo ==========================================
  echo NOT READY: %ERR% check(s) failed.
  echo ==========================================
  exit /b 1
)
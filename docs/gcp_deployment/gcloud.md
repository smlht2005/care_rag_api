https://care-rag-api-441535054378.asia-east1.run.app

gcloud projects describe gen-lang-client-0567547134 --format=value(projectNumber)


查詢care-rag-api 流量,最新就緒 revision

```
gcloud run services describe care-rag-api ^
  --region asia-east1 ^
  --project gen-lang-client-0567547134 ^
  --format="yaml(status.latestReadyRevisionName,status.traffic)"
```
==>
status:
  latestReadyRevisionName: care-rag-api-00011-dzr
  traffic:
  - latestRevision: true
    percent: 100
    revisionName: care-rag-api-00011-dzr

```
gcloud run services describe care-rag-line-proxy ^
  --region asia-east1 ^
  --project gen-lang-client-0567547134 ^
  --format="yaml(status.latestReadyRevisionName,status.traffic)"

```
==>
status:
  latestReadyRevisionName: care-rag-line-proxy-00009-pct
  traffic:
  - latestRevision: true
    percent: 100
    revisionName: care-rag-line-proxy-00009-pct
----------------
```
gcloud run services describe care-rag-api --region asia-east1 --project gen-lang-client-0567547134 --format="table(status.traffic[].revisionName,status.traffic[].percent,status.traffic[].latestRevision)"
```
==>
REVISION_NAME: ['care-rag-api-00011-dzr']
PERCENT: [100]
LATEST_REVISION: [True]





更新使用最新版本!
```
gcloud run services update-traffic care-rag-api ^
  --project gen-lang-client-0567547134 ^
  --region asia-east1 ^
  --to-latest
```


# Liquidity Gate Infrastructure Requirements

## Storage Account Configuration

The function app uses identity-based authentication with storage account `stliquidityfunc01`.

**Required Settings:**
- `publicNetworkAccess`: **Enabled** (or configure private endpoints)
- Function app managed identity needs these RBAC roles on the storage account:
  - Storage Blob Data Owner
  - Storage Queue Data Contributor
  - Storage Table Data Contributor

## Fix Commands (if MCP stops working)

```bash
# 1. Enable public network access on storage
az storage account update --name stliquidityfunc01 --resource-group rg-openai --public-network-access Enabled

# 2. Get function app identity
PRINCIPAL_ID=$(az functionapp identity show --name liquidity-gate-func --resource-group rg-openai --query principalId -o tsv)

# 3. Assign RBAC roles
STORAGE_ID="/subscriptions/a20bc194-9787-44ee-9c7f-7c3130e651b6/resourceGroups/rg-openai/providers/Microsoft.Storage/storageAccounts/stliquidityfunc01"

az role assignment create --assignee $PRINCIPAL_ID --role "Storage Blob Data Owner" --scope $STORAGE_ID
az role assignment create --assignee $PRINCIPAL_ID --role "Storage Queue Data Contributor" --scope $STORAGE_ID
az role assignment create --assignee $PRINCIPAL_ID --role "Storage Table Data Contributor" --scope $STORAGE_ID

# 4. Restart function app
az functionapp restart --name liquidity-gate-func --resource-group rg-openai
```

## PostgreSQL Database

Database `treasurydb` must be running:
```bash
az postgres flexible-server start --resource-group rg-openai --name treasurydb
```

## MCP Endpoint

- URL: `https://liquidity-gate-func.azurewebsites.net/runtime/webhooks/mcp/sse`
- Auth: `x-functions-key` with `mcp_extension` system key
- Key: Retrieve with: `az functionapp keys list --name liquidity-gate-func --resource-group rg-openai --query "systemKeys.mcp_extension" -o tsv`

## Verification

```bash
# Test ping
curl https://liquidity-gate-func.azurewebsites.net/api/ping

# Test MCP SSE (replace <KEY> with mcp_extension key)
curl "https://liquidity-gate-func.azurewebsites.net/runtime/webhooks/mcp/sse?code=<KEY>"
```

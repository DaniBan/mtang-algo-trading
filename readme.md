# Install Requirements
Using pip:
`
pip install -e .
`

Using uv:
`
uv pip install -e .
`

- uv is much faster and has better dependency resolution
- `pip install uv`

Install TA-Lib binaries from https://ta-lib.org/install/#executable-installer-recommended

For env configs create a ".env" file with the following structure:
```
ACCOUNT_ID=<your trading account id>
PASSWORD=<your trading account password>
MT5_SERVER=<Meta Trader 5 server>  # A server accessible by your account, "OANDA-Demo-1" for example
```
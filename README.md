# Map of EMIS and TPP in England

EMIS and TPP are the two major GP System Suppliers to the NHS in England.

This map is updated weekly[^1] to show their coverage at a PCN level.

![PCN Map](output/pcn_map.png)

[Download the data as a CSV](output/pcn_system_supplier_counts_with_icb.csv)

[^1]: <sub> (unless there are bugs in the code, or the sources we scape have changed -- check the [action log](https://github.com/sebbacon/gpss-map/actions) to verify)

## Development notes

Something about the NHS England setup changed in summer 2024, and it started returning a 403 to Github Actions.

Therefore, the `grab.py` now uses a cloudflare worker, saved as a dev workflow to Seb's CF account, to get that file.

That's not committed to this repo as I'm relying on its name being secret to help avoid third parties using it (because I can't be bothered to work out how to secure it properly)

The free plan allows up to 100,000 requests per day, and the worker is set to cache responses for 24 hours.

The worker domain comes from a CF_WORKER_DOMAIN environment variable, stored as a secret in Github Actions.

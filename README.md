# Boiler device registry

This independent repository discovers device packages; it contains no hardware
modification script or model runtime. Packages remain in their model repository.
The initial OXP3 entry uses the existing `FlightDan/OneXPlayer3-SteamOS` repository
and preserves all of its historical releases.

`device-index.json` follows DeviceIndex schema version 1. Sequence numbers are
monotonic, revocations refer to manifest SHA-256 values, and each production
package must carry a pinned source and verified manifest digest. The current
index is unsigned and intentionally advertises no production package. A key or
release URL is never invented to make a draft look published.

`devices/oxp3.json` distinguishes existing legacy release support, experimental
Boiler migration and blocked combinations. Evidence, notes and known limitations
travel with the device record. Claims for an old release do not certify a newly
packaged bridge.

Build a local development index from a real package directory:

```sh
python scripts/build-index.py --package ../Boiler-oxp3/dist/device-oxp3 --output dist/device-index.dev.json
```

The command calculates the manifest digest and every inventory digest before
adding a local-only source. It never signs, uploads or changes the production
index. An authenticated production index and accepted model package are release
gates. Boiler's generic installer consumes an authenticated index or a visible,
explicit local development trust grant.

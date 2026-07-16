# [0.7.0](https://github.com/CampAsAChamp/plextraktbox/compare/v0.6.0...v0.7.0) (2026-07-16)


### Bug Fixes

* patch undici CVE-2026-12151 in Node build images ([7c780eb](https://github.com/CampAsAChamp/plextraktbox/commit/7c780eb4d5b4e7244d0759b3f1cc3081e4cf89a1))
* surface log stream and notification errors ([589cd58](https://github.com/CampAsAChamp/plextraktbox/commit/589cd586c09f58efc2391d9c6c2220b86c861886))
* switch Python runtime to alpine for fewer CVEs ([ef68f47](https://github.com/CampAsAChamp/plextraktbox/commit/ef68f475d2f4f3b694b425213cb9d039df0d0f2b))


### Features

* add SQLite backup restore ([109da26](https://github.com/CampAsAChamp/plextraktbox/commit/109da2675daac9fe4b3cd21c9c8e7f68308f062c))
* allow configuring HTTP listen port via PORT ([53c0418](https://github.com/CampAsAChamp/plextraktbox/commit/53c0418777e4d4a24bd67aec85322639ee275fd9))

# [0.6.0](https://github.com/CampAsAChamp/plextraktbox/compare/v0.5.0...v0.6.0) (2026-07-16)


### Features

* add PUID/PGID mounts and opt-in corporate CA for Docker ([7f331f2](https://github.com/CampAsAChamp/plextraktbox/commit/7f331f2bfbd2e8eab4973034007ef85da6290a61))

# [0.5.0](https://github.com/CampAsAChamp/plextraktbox/compare/v0.4.0...v0.5.0) (2026-07-15)


### Bug Fixes

* restore APScheduler import-untyped ignores ([9541f75](https://github.com/CampAsAChamp/plextraktbox/commit/9541f75b857122d30b8870e7527109fa6c7fcf73))


### Features

* add sync cache models and migration ([b61ca17](https://github.com/CampAsAChamp/plextraktbox/commit/b61ca17325731b40af259f8fef9df2c5f3ff708e))
* add Sync caches settings UI ([686a2ce](https://github.com/CampAsAChamp/plextraktbox/commit/686a2ce4fbff689d4725d5e4d9db799ba4f60019))
* implement sync cache services ([2b65b00](https://github.com/CampAsAChamp/plextraktbox/commit/2b65b00b0b4865e2fbd4be1dd273484d824e7f97))
* wire sync caches into sources and settings API ([55d482b](https://github.com/CampAsAChamp/plextraktbox/commit/55d482bce4a06d75e00b42974d5a51cdc9d6695c))

# [0.4.0](https://github.com/CampAsAChamp/plextraktbox/compare/v0.3.1...v0.4.0) (2026-07-15)


### Bug Fixes

* match AppLayout GitHub menu item label in test ([cc8f963](https://github.com/CampAsAChamp/plextraktbox/commit/cc8f963c8e0996b4338c6140215c9aedf8eab598))
* treat up-dev Ctrl+C as a clean stop ([fe2bf21](https://github.com/CampAsAChamp/plextraktbox/commit/fe2bf216cee02fd109625ef61f527d36475a5f52))
* use dict.fromkeys for colorless HTTP method styles ([b2e42a3](https://github.com/CampAsAChamp/plextraktbox/commit/b2e42a3296c7dec83803d07bb151908b443760d3))
* wait for compose teardown on up-dev Ctrl+C ([f7b00a8](https://github.com/CampAsAChamp/plextraktbox/commit/f7b00a86550430db8379c6002791dd3964dade4e))


### Features

* add selectable UI themes on the frontend ([0ab1e8b](https://github.com/CampAsAChamp/plextraktbox/commit/0ab1e8b2aa6c79cd5d656f67079030a68014d01f))
* add theme catalog API and persist ui_theme ([af61249](https://github.com/CampAsAChamp/plextraktbox/commit/af61249f78839b376d55d3069e453dad83c5d812))
* add theme picker to Settings ([be8a198](https://github.com/CampAsAChamp/plextraktbox/commit/be8a19847109e94402d95adcdbad5187d442a1f9))
* color HTTP methods in console access logs ([0d8998a](https://github.com/CampAsAChamp/plextraktbox/commit/0d8998aa2ccbe1877252e1c9505b1e05e7dd75f7))
* hide healthy API badge and link GitHub in account menu ([9672868](https://github.com/CampAsAChamp/plextraktbox/commit/9672868ce4a8e0078c94f05dcf43f74be6553105))

## [0.3.1](https://github.com/CampAsAChamp/plextraktbox/compare/v0.3.0...v0.3.1) (2026-07-15)


### Bug Fixes

* mobile layout ([010edc0](https://github.com/CampAsAChamp/plextraktbox/commit/010edc0b7414722f2731fc84ed79f87fa1e0e48d))

# [0.3.0](https://github.com/CampAsAChamp/plextraktbox/compare/v0.2.1...v0.3.0) (2026-07-15)


### Features

* add mobile layout ([436b128](https://github.com/CampAsAChamp/plextraktbox/commit/436b128e8506213e029fa151b79b81b4544e4e7d))

# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

semantic-release maintains this file from Conventional Commits on `main`.

## [0.2.1](https://github.com/CampAsAChamp/plextraktbox/compare/v0.2.0...v0.2.1) (2026-07-15)


### Bug Fixes

* stop hardcoding package version in unit test ([c2f78ae](https://github.com/CampAsAChamp/plextraktbox/commit/c2f78aed1a0ba87ec887b6f2372dd7a7190867bc))
* use one app version across release-please targets ([3c00bb4](https://github.com/CampAsAChamp/plextraktbox/commit/3c00bb4ea786203ff1352d27cab46d8a8b49b214))

## [0.2.0](https://github.com/CampAsAChamp/plextraktbox/compare/v0.1.0...v0.2.0) (2026-07-15)


### Features

* bootstrap first release-please release ([42c39ea](https://github.com/CampAsAChamp/plextraktbox/commit/42c39ea11f4914b135cb8c9bc9d347aa0208cbab))


### Bug Fixes

* keep release-please changelog under backend ([3de18de](https://github.com/CampAsAChamp/plextraktbox/commit/3de18de69f4dd0fd1bde4230c7ecd72d8a443461))

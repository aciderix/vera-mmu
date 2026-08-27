# Contribuer à VERA-MMU

Merci de contribuer à VERA-MMU. Le projet accepte les corrections, tests, documents, Domain Packs et améliorations qui préservent le Core générique, les invariants de sécurité et la frontière project-local.

## Règles d’entrée

Une contribution doit être ciblée, accompagnée de tests adaptés et ne doit jamais modifier les corpus ou assertions pour forcer un résultat. Les modifications Core ne peuvent pas introduire de vocabulaire, d’outil, de binaire, de réseau ou de doctrine ARET ; ces éléments restent confinés à `src/vera_mmu/domain_packs/aret/` ou à un Domain Pack dédié.

Toute écriture de configuration d’hôte doit conserver le protocole VERA : **preview → vérification de fraîcheur → confirmation explicite → écriture atomique ou refus**. Une contribution ne doit jamais exposer au frontend un shell libre, un chemin libre, une capacité native générique, un verdict ou un contenu de configuration de confiance.

## DCO — Developer Certificate of Origin 1.1

En ajoutant `Signed-off-by: Nom <email>` à chaque commit proposé, le contributeur certifie :

```text
Developer's Certificate of Origin 1.1

By making a contribution to this project, I certify that:

(a) The contribution was created in whole or in part by me and I have the
    right to submit it under the open source license indicated in the file; or

(b) The contribution is based upon previous work that, to the best of my
    knowledge, is covered under an appropriate open source license and I have
    the right under that license to submit that work with modifications,
    whether created in whole or in part by me, under the same open source
    license (unless I am permitted to submit under a different license), as
    indicated in the file; or

(c) The contribution was provided directly to me by some other person who
    certified (a), (b) or (c) and I have not modified it.

(d) I understand and agree that this project and the contribution are public
    and that a record of the contribution (including all personal information
    I submit with it, including my sign-off) is maintained indefinitely and may
    be redistributed consistent with this project or the open source license(s)
    involved.
```

La commande usuelle est `git commit -s`. Une contribution volontairement soumise au projet est distribuée sous Apache-2.0, sauf accord séparé écrit.

## Domain Packs et sources externes

Tout import ou portage doit déclarer son origine, son commit, les chemins concernés, les hashes, les crédits et sa licence. Aucune source ARET-MMU n’est intégrée implicitement dans le Core VERA. Une contribution dont les droits ou la compatibilité de licence ne sont pas démontrés est refusée.

## Vérifications minimales

Exécuter `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m pytest -q` avant une proposition. Les changements desktop ou d’archives doivent aussi conserver la matrice Windows/Linux native et les tests de conformance.

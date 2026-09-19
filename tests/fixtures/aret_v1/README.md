# Références ARET V1 — données de test, jamais du code de production

Ce répertoire contient des **copies de référence** issues du dépôt `aciderix/ARET-MMU`, commit
`b9511dccc811b5fc2efaf26a7a3cfc941c0e5754`. Elles n'existent que pour donner aux tests de parité un
second implémenteur et des données réelles contre lesquels comparer, afin que la comparaison porte
sur le comportement V1 observé et non sur l'idée qu'on s'en fait.

| Fichier | Origine | Rôle |
|---|---|---|
| `addressing_reference.py` | `aret-memory/core/addressing.py`, copie octet pour octet | Second implémenteur du test de parité `C01` |
| `baseline_addresses.json` | 22 adresses `ARET://` extraites de `aret-memory/.aret-memory/aret_memory.sqlite` | Corpus réel du test de parité `C01` |

**Deux règles.**

1. `tests/test_aret_c01_addressing_parity.py` épingle le SHA-256 de `addressing_reference.py` et la
   taille et le SHA-256 de la mémoire baseline dont les adresses proviennent. Si l'une dérive, le
   test échoue plutôt que de comparer VERA à une référence périmée en silence.
2. **Rien dans `src/vera_mmu/` ne doit lire ce répertoire.** Le Core ne connaît pas ARET ; c'est la
   propriété que `C01` doit démontrer, pas une qu'il peut supposer.

La mémoire baseline elle-même n'est pas versionnée ici : 11 Mo de SQLite pour vingt-deux adresses
serait payer cher une donnée que l'on peut extraire et attester par son empreinte.

## Ajouts pour `C03`

| Fichier | Origine | Rôle |
|---|---|---|
| `schema/00{1..6}_*.sql` | `aret-memory/schema/`, copies octet pour octet | DDL réel qui **construit** la source des tests, au lieu d’un `CREATE TABLE` réécrit à la main |
| `baseline_components.json` | 17 composants, 520 liens de connaissance et 9 symboles extraits de la même mémoire | Corpus réel du test de parité `C03` |

Le point important n’est pas que ces fichiers existent, c’est ce qu’ils remplacent. Les fixtures de
composant écrivaient leur propre `CREATE TABLE component`, non `STRICT` et sans `DEFAULT ''`, puis
vérifiaient la conformité contre `aret_v1_schema_manifest()` — une déclaration VERA du schéma ARET
que rien n’avait jamais comparée au schéma réel. Une fixture écrite d’après le contrat qu’elle sert à
valider ne peut pas le réfuter.

## Ajouts pour `C02`

| Fichier | Origine | Rôle |
|---|---|---|
| `source/repository_reference.py` | `aret-memory/core/repository.py`, copie octet pour octet | Source dont `C02` **extrait** les faits par analyse syntaxique : précédence de résolution, lecture de l’environnement, création des répertoires |
| `source/git_memory_reference.py` | `aret-memory/ops/git_memory.py`, copie octet pour octet | Référence du checkpoint WAL et du confinement Git ; **exécutée** par `C13`, voir plus bas |

Ces deux fichiers sont volumineux — 148 Ko et 12 Ko — et c’est assumé : ils sont la seule façon de
vérifier une déclaration de layout autrement qu’en relisant une transcription. `C02` n’en lit aucun
texte à la main : il parcourt l’arbre syntaxique de `MemoryStore.__init__` pour en tirer les
constantes et les appels. Une transcription fidèle ne prouverait que la fidélité de la copie.

## Ajouts pour `C09`, `C10` et `C11`

| Fichier | Origine | Rôle |
|---|---|---|
| `source/mcp_server_reference.py` | `aret-memory/aret_mmu_server.py`, copie octet pour octet | Source unique des trois couplages : la doctrine statique, les 44 outils, la racine imposée |

Les trois la citent et aucun ne la transcrit : `tests/aret_v1_server_reference.py` en extrait les
outils, leurs paramètres et les constantes de module par analyse syntaxique. Une copie par couplage
aurait divergé ; trois transcriptions de ce qu'elle fait auraient prouvé trois copier-collers.

## `C13` : la même source, mais exécutée

`source/git_memory_reference.py` sert deux couplages de deux façons. `C02` en lit l'arbre syntaxique
pour épingler ce que son checkpoint WAL contrôle. `C13` le **charge comme module** — par
`tests/aret_v1_git_reference.py` — et fait tourner ses fonctions sur de vrais dépôts Git montés pour
l'occasion. La question de `C13` porte sur un comportement devant un dépôt réel, et aucune lecture
de code n'y répond.

C'est ce qui a fait tomber le défaut consigné dans `LOG-0312` : `invoke()` applique `.strip()` à la
sortie entière de `git status --porcelain=v1`, `changes()` découpe ensuite à position fixe, et un
fichier de la mémoire est déclaré hors de la mémoire. **Ce fichier ne doit pas être corrigé.** Une
référence réparée mesurerait autre chose qu'ARET ; le test de hash tombe si on y touche, et c'est
voulu.

## `C14` : le `MemoryStore` entier, exécuté

`C14` va un cran plus loin que `C13`. Ce n'est plus une fonction isolée qui tourne, c'est le
`MemoryStore` d'ARET au complet, chargé par `tests/aret_v1_repository_reference.py` et migré sur son
propre DDL. Le layout versionné le permet sans rien modifier : `_migrate` et `_bundle_migrations`
cherchent leur schéma à `Path(__file__).parents[1] / "schema"`, ce qui, depuis `source/`, désigne
exactement le `schema/` voisin et ses six migrations réelles.

La seule dépendance externe du dépôt est `core.addressing`. La référence d'adressage versionnée pour
`C01` est présentée sous ce nom, **avec son empreinte épinglée elle aussi** : charger un autre
adressage ferait tourner un ARET qui n'est pas celui qu'on croit mesurer.

Ce qui en est sorti est consigné dans `LOG-0315` : la chaîne d'intégrité d'ARET tient sur huit
altérations, mais son manifeste ne porte aucune identité de projet, et le `source_device_id` qu'il
écrit n'est relu nulle part.

## `C06` : l'adaptateur de pipelines

| Fichier | Origine | Rôle |
|---|---|---|
| `source/pipelines_reference.py` | `aret-memory/evidence/adapters/pipelines.py`, copie octet pour octet | Catalogue de 27 pipelines, exécuté en dry-run par `C06` |

Il importe `core.repository`, satisfait par la référence de dépôt déjà chargeable pour `C14` : ARET
tourne donc contre son vrai `MemoryStore` et son vrai DDL. `PROJECT_ROOT` y est déclaré et n'est
utilisé nulle part — vérifié sur la source entière — donc le déplacement du fichier ne change rien
à son comportement.

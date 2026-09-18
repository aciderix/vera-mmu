/**
 * Reading a capability contract the Core composed, and nothing more.
 *
 * Like `journey.ts`, this module holds the only contract logic the interface is allowed to have:
 * splitting what an operator typed into a list, reading the closed catalogues the Core published,
 * and reading the refusals it named. No rule is decided here. Which runners exist, which policies
 * are declarable, whether a declaration is refused and why — all of it is derived in
 * `vera_mmu/capability_builder.py` and `vera_mmu/project_catalogs.py`, and merely displayed.
 *
 * Two refusals of its own, and they are the same one twice: absent information is never turned
 * into a decision. A catalogue the Core has not published yet yields no choices rather than a
 * hard-coded fallback, and a preview carrying no refusal list is read as *unknown*, never as
 * "nothing refused".
 */

export type ContractRefusal = { code: string; message: string };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** Split one comma-separated field into the list the Core will judge; nothing is validated here. */
export function asList(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter((item) => item.length > 0);
}

/**
 * Read one closed catalogue the Core published. An entry is either a plain identifier or an
 * object carrying `id`; anything else is discarded rather than guessed at.
 */
export function asChoices(options: Record<string, unknown> | null, key: string): string[] {
  if (!isRecord(options) || !Array.isArray(options[key])) return [];
  return (options[key] as unknown[])
    .map((item) => (typeof item === "string" ? item : isRecord(item) && typeof item.id === "string" ? item.id : ""))
    .filter((item) => item.length > 0);
}

/** The refusals the Core named, with their codes, so a screen states the reason. */
export function asRefusals(preview: Record<string, unknown> | null): ContractRefusal[] {
  if (!isRecord(preview) || !Array.isArray(preview.refusals)) return [];
  return (preview.refusals as unknown[])
    .filter(isRecord)
    .map((item) => ({
      code: typeof item.code === "string" ? item.code : "REFUSED",
      message: typeof item.message === "string" ? item.message : "",
    }));
}

/**
 * Whether a reviewed contract may be confirmed.
 *
 * A preview the Core did not mark `PREVIEW` is never confirmable, so an unknown or missing
 * status closes the button. Refusing on absent information is the safe direction here, and it is
 * the opposite of `journey.ts` on purpose: a journey not yet read locks nothing, because locking
 * there would hide a panel; a contract not yet reviewed writes nothing, because confirming here
 * would write to the project.
 */
export function isConfirmable(preview: Record<string, unknown> | null): boolean {
  if (!isRecord(preview)) return false;
  return preview.status === "PREVIEW" && asRefusals(preview).length === 0;
}

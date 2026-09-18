/**
 * Reading a gate report the Core derived, and nothing more.
 *
 * §33 asks the screen to show clearly the difference between technical validation, semantic
 * appreciation and simple observation. That difference is decided in `vera_mmu/evidence_classes.py`
 * and enforced at promotion; here it is only read. Nothing in this module may conclude that
 * something is a technical validation — only repeat that the Core said so.
 *
 * Hence the two refusals it does carry, both in the same direction: an unreadable class is never
 * shown as a technical validation, and a missing promotion flag is never read as "yes". Absence
 * goes to the side that claims less.
 */

export type EvidenceClass = "TECHNICAL_VALIDATION" | "SIMPLE_OBSERVATION" | "SEMANTIC_APPRECIATION" | "UNKNOWN";

export type GateRequirement = {
  evidenceId: string;
  evidenceType: string;
  evidenceClass: EvidenceClass;
  verdict: string;
  admission: string;
  primary: boolean;
  mayCreateProof: boolean;
  reason: string;
};

export type PromotionLines = { canSatisfyGate: boolean; canCreateProof: boolean; satisfactionReason: string; proofReason: string };

const CLASSES = ["TECHNICAL_VALIDATION", "SIMPLE_OBSERVATION", "SEMANTIC_APPRECIATION"] as const;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function text(value: unknown, fallback: string): string {
  return typeof value === "string" && value.length > 0 ? value : fallback;
}

/** Read the requirements the Core classified, keeping every entry it sent. */
export function readRequirements(report: Record<string, unknown> | null): GateRequirement[] {
  if (!isRecord(report) || !Array.isArray(report.requirements)) return [];
  return (report.requirements as unknown[]).filter(isRecord).map((item) => {
    const declared = String(item.evidence_class);
    // An unreadable class is never promoted to a technical validation by this screen.
    const evidenceClass: EvidenceClass = (CLASSES as readonly string[]).includes(declared)
      ? (declared as EvidenceClass)
      : "UNKNOWN";
    return {
      evidenceId: text(item.evidence_id, ""),
      evidenceType: text(item.evidence_type, "INCONNU"),
      evidenceClass,
      verdict: text(item.verdict, "UNKNOWN"),
      admission: text(item.admission, "NOT_DECIDED"),
      primary: item.primary === true,
      // And a capability it cannot read is never announced as able to found a proof.
      mayCreateProof: evidenceClass === "TECHNICAL_VALIDATION" && item.may_create_proof === true,
      reason: text(item.reason, ""),
    };
  }).filter((item) => item.evidenceId.length > 0);
}

/** The two lines §33 shows under « Promotion », read strictly. */
export function readPromotion(report: Record<string, unknown> | null): PromotionLines {
  const absent: PromotionLines = {
    canSatisfyGate: false,
    canCreateProof: false,
    satisfactionReason: "Gate non lue.",
    proofReason: "Gate non lue.",
  };
  if (!isRecord(report) || !isRecord(report.promotion)) return absent;
  const promotion = report.promotion;
  return {
    canSatisfyGate: promotion.can_satisfy_gate === true,
    canCreateProof: promotion.can_create_proof === true,
    satisfactionReason: text(promotion.satisfaction_reason, absent.satisfactionReason),
    proofReason: text(promotion.proof_reason, absent.proofReason),
  };
}

/** How many requirements fall in each class, for the summary §33 asks to be legible at a glance. */
export function countByClass(requirements: GateRequirement[]): Record<EvidenceClass, number> {
  const counts: Record<EvidenceClass, number> = {
    TECHNICAL_VALIDATION: 0,
    SIMPLE_OBSERVATION: 0,
    SEMANTIC_APPRECIATION: 0,
    UNKNOWN: 0,
  };
  for (const requirement of requirements) counts[requirement.evidenceClass] += 1;
  return counts;
}

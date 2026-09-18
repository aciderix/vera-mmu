/** Interface desktop VERA : seules les commandes Rust typées sont accessibles au React local. */
import { invoke } from "@tauri-apps/api/core";

export type JsonObject = Record<string, unknown>;

export const desktopApi = {
  selectProject: () => invoke<JsonObject>("select_project"),
  scanProject: () => invoke<JsonObject>("scan_project"),
  wizardState: () => invoke<JsonObject>("wizard_state"),
  recommendProfile: () => invoke<JsonObject>("recommend_profile"),
  projectStatus: () => invoke<JsonObject>("project_status"),
  projectDoctor: () => invoke<JsonObject>("project_doctor"),
  migrationStatus: () => invoke<JsonObject>("migration_status"),
  projectDocumentation: () => invoke<JsonObject>("project_documentation"),
  profileRebindPreview: (projectId: string, projectName: string, projectDomain: string, projectDescription: string) =>
    invoke<JsonObject>("profile_rebind_preview", { projectId, projectName, projectDomain, projectDescription }),
  profileRebindApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("profile_rebind_apply", { previewHash, confirm }),
  profileRebindRecoveryPreview: () =>
    invoke<JsonObject>("profile_rebind_recovery_preview"),
  profileRebindRecoveryApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("profile_rebind_recovery_apply", { previewHash, confirm }),
  capabilityOptions: () => invoke<JsonObject>("capability_options"),
  /** The complete §32 contract. No command, API, URL or path parameter exists: the Core holds none. */
  capabilityPreview: (contract: {
    identifier: string;
    name: string;
    description: string;
    kind: string;
    version: string;
    runner: string;
    policy: string;
    timeoutSeconds: number | null;
    inputs: string[];
    outputs: string[];
    artifacts: string[];
    validator: string;
    yieldsProof: boolean;
    confirmationRequired: boolean;
    gateBacked: boolean;
  }) => invoke<JsonObject>("capability_preview", contract),
  capabilityApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("capability_apply", { previewHash, confirm }),
  policyOptions: () => invoke<JsonObject>("policy_options"),
  /** Named policy lines only; which values are declarable is the Core's to say. */
  policyPreview: (changes: Record<string, string | string[]>) =>
    invoke<JsonObject>("policy_preview", { changes }),
  policyApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("policy_apply", { previewHash, confirm }),
  resumeOptions: () => invoke<JsonObject>("resume_options"),
  /** The resume contract and the enabled integrations; the Core says what a change invalidates. */
  resumePreview: (edit: {
    template: string | null;
    sections: { id: string; required: boolean }[] | null;
    maxResumeBytes: number | null;
    integrations: string[] | null;
  }) => invoke<JsonObject>("resume_preview", edit),
  resumeApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("resume_apply", { previewHash, confirm }),
  /** One declared gate as §33 displays it: classified requirements and the promotion lines. */
  gateReport: (gateId: string) => invoke<JsonObject>("gate_report", { gateId }),
  gatePolicyPreview: (gateId: string, mode: string, minimumAdmissions: number | null) =>
    invoke<JsonObject>("gate_policy_preview", { gateId, mode, minimumAdmissions }),
  gatePolicyApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("gate_policy_apply", { previewHash, confirm }),
  gateStructurePreview: (gateId: string, workItemId: string, primaryEvidenceId: string, requirementEvidenceIds: string[]) =>
    invoke<JsonObject>("gate_structure_preview", { gateId, workItemId, primaryEvidenceId, requirementEvidenceIds }),
  gateStructureApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("gate_structure_apply", { previewHash, confirm }),
  initializationPreview: (template: string, projectId: string, projectName: string) =>
    invoke<JsonObject>("initialization_preview", { template, projectId, projectName }),
  initializationApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("initialization_apply", { previewHash, confirm }),
  agents: () => invoke<JsonObject>("agent_profiles"),
  generation: (agentProfileId: string) => invoke<JsonObject>("generation_preview", { agentProfileId }),
  stage: (agentProfileId: string, confirm: boolean) => invoke<JsonObject>("stage_adapter", { agentProfileId, confirm }),
  installationPreview: (agentProfileId: string) =>
    invoke<JsonObject>("installation_preview", { agentProfileId }),
  installationApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("installation_apply", { previewHash, confirm }),
  doctor: (agentProfileId: string) => invoke<JsonObject>("adapter_doctor", { agentProfileId }),
  memorySync: () => invoke<JsonObject>("memory_sync"),
};

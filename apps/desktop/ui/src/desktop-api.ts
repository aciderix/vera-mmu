/** Interface desktop VERA : seules les commandes Rust typées sont accessibles au React local. */
import { invoke } from "@tauri-apps/api/core";

export type JsonObject = Record<string, unknown>;

export const desktopApi = {
  selectProject: () => invoke<JsonObject>("select_project"),
  scanProject: () => invoke<JsonObject>("scan_project"),
  projectStatus: () => invoke<JsonObject>("project_status"),
  profileRebindPreview: (projectId: string, projectName: string, projectDomain: string, projectDescription: string) =>
    invoke<JsonObject>("profile_rebind_preview", { projectId, projectName, projectDomain, projectDescription }),
  profileRebindApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("profile_rebind_apply", { previewHash, confirm }),
  profileRebindRecoveryPreview: () =>
    invoke<JsonObject>("profile_rebind_recovery_preview"),
  profileRebindRecoveryApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("profile_rebind_recovery_apply", { previewHash, confirm }),
  capabilityPreview: (identifier: string, name: string, kind: string, version: string, description: string) =>
    invoke<JsonObject>("capability_preview", { identifier, name, kind, version, description }),
  capabilityApply: (previewHash: string, confirm: boolean) =>
    invoke<JsonObject>("capability_apply", { previewHash, confirm }),
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

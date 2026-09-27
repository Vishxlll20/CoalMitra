import { create } from "zustand";
import type { Role } from "../types";

const ROLES: { key: Role; label: string; blurb: string }[] = [
  { key: "GEOLOGIST", label: "Geologist", blurb: "Field data, seams, raw documents" },
  { key: "MINISTRY_OFFICIAL", label: "Ministry Official", blurb: "Consolidated reports & ready answers" },
  { key: "AUDITOR", label: "Auditor", blurb: "Traceability, confidence, anomaly trails" },
];

interface RoleState {
  role: Role;
  roleMeta: (typeof ROLES)[number];
  setRole: (r: Role) => void;
}

export const useRoleStore = create<RoleState>((set) => ({
  role: "GEOLOGIST",
  roleMeta: ROLES[0],
  setRole: (role) => {
    set({ role, roleMeta: ROLES.find((r) => r.key === role)! });
  },
}));

export { ROLES };
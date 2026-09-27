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
  role: (localStorage.getItem("coalmitra.role") as Role) || "GEOLOGIST",
  roleMeta: ROLES[(localStorage.getItem("coalmitra.role") as Role) === "MINISTRY_OFFICIAL" ? 1 : (localStorage.getItem("coalmitra.role") as Role) === "AUDITOR" ? 2 : 0],
  setRole: (role) => {
    localStorage.setItem("coalmitra.role", role);
    set({ role, roleMeta: ROLES.find((r) => r.key === role)! });
  },
}));

export { ROLES };
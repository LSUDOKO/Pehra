// Supervisors view, approve and tighten their own site's plan.
@id("supervisor-manage-own-plan")
permit (
  principal is Supervisor,
  action in [Action::"ViewPlan", Action::"ApprovePlan", Action::"StrictenPlan", Action::"OverridePlan"],
  resource is Plan
) when { resource.site.owner == principal };

// Supervisors may loosen their own plan only with a written reason (>= 10 chars).
@id("supervisor-loosen-with-reason")
permit (
  principal is Supervisor,
  action == Action::"LoosenPlan",
  resource is Plan
) when { resource.site.owner == principal && context.reason_length >= 10 };

// The AI agent can read plans and make them stricter.
@id("agent-view-and-stricten")
permit (
  principal is SystemAgent,
  action in [Action::"ViewPlan", Action::"StrictenPlan"],
  resource is Plan
);

// The AI agent can never loosen or override a plan. Forbid always wins over permit.
@id("agent-never-loosens")
forbid (
  principal is SystemAgent,
  action in [Action::"LoosenPlan", Action::"OverridePlan"],
  resource
);

// No one may loosen without a reason, whatever their role.
@id("no-loosen-without-reason")
forbid (
  principal,
  action == Action::"LoosenPlan",
  resource
) unless { context.reason_length >= 10 };

// Contractors may view plans of sites in their own tenant.
@id("contractor-view-tenant-plans")
permit (
  principal is Contractor,
  action == Action::"ViewPlan",
  resource is Plan
) when { principal.tenant == resource.site.tenant };

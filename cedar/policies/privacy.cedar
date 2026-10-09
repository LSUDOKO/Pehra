// Workers (anonymous token) can log check-ins only at their own site.
@id("worker-checkin-own-site")
permit (
  principal is Worker,
  action == Action::"LogCheckIn",
  resource is Site
) when { principal.site == resource };

// Contractors see aggregates for their own tenant's sites.
@id("contractor-aggregates")
permit (
  principal is Contractor,
  action == Action::"ViewCheckInsAggregate",
  resource is Site
) when { principal.tenant == resource.tenant };

// Labour officers see aggregates only.
@id("labour-officer-aggregates")
permit (
  principal is LabourOfficer,
  action == Action::"ViewCheckInsAggregate",
  resource is Site
);

// Supervisors see their own site's raw check-ins and aggregates.
@id("supervisor-own-checkins")
permit (
  principal is Supervisor,
  action in [Action::"ViewCheckInsRaw", Action::"ViewCheckInsAggregate"],
  resource is Site
) when { resource.owner == principal };

// Nobody else ever sees raw check-ins.
@id("raw-checkins-supervisor-only")
forbid (
  principal,
  action == Action::"ViewCheckInsRaw",
  resource
) unless { principal is Supervisor && resource is Site && resource.owner == principal };

// Daily records: the site supervisor and contractors of the same tenant.
@id("records-read")
permit (
  principal,
  action == Action::"ReadRecord",
  resource is Record
) when {
  (principal is Supervisor && resource.site.owner == principal) ||
  (principal is Contractor && principal.tenant == resource.site.tenant)
};

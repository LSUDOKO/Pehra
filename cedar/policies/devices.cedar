// A sensor can write readings only for the site or household it was registered to.
@id("device-post-own-stream")
permit (
  principal is Device,
  action == Action::"PostReading",
  resource is SensorStream
) when { principal.owner == resource.owner };

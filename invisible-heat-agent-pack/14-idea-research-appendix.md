# 14 · Appendix: how this idea was chosen

Background only. The build does not depend on anything here. Firecrawl had no credits in the research session, so novelty checks used alphaXiv and ordinary web search and are **not exhaustive**.

## Existing projects found (avoid duplicating)

- Sky-photo AQI apps: Air Cognizer (Delhi students, free on Play Store) and a USC project already do this.
- Waterlogging reporting by photo: Patna Smart City launched one; Indore's High Court pushed its city to add one.
- Sewer sensors and drain monitoring: Gurugram fitting AIResQ sensors; Mumbai AI monitoring of desilting.
- Water tanker GPS tracking: Delhi 1,111 GPS tankers and Jal Board app.
- Groundwater and well apps: MyWell, Million Wells, JalDrishti.
- Plain AQI dashboards: everywhere.

## Ideas considered (all tracks)

| Idea | Track | Verdict |
|---|---|---|
| **Invisible Heat** (this project) | Heat and Water | **Chosen.** Highest impact, public data, software-only, strong story, natural AWS fit. |
| JalDhwani: phone sonar for tank level (near-ultrasound chirp, FMCW dechirp on Web Audio) | Heat and Water | Best physical-device idea; risk is phone speaker/mic limits above ~18 kHz (expect 1–2 cm accuracy); needs a go/no-go test with a bucket and a ruler. Fallback or follow-up. |
| Raat Reading: meter photo at night and morning to detect hidden leaks (Textract) | Heat and Water | Best zero-hardware fallback. |
| VayuDrishti: camera-based AQI | Air | Skipped; Air Cognizer exists. |
| PuddleGauge: flood depth from submerged wheels | Heat and Water | Needs monsoon footage; hard waterline segmentation. |
| DrainGuard: drain water-level sensor + anomaly alerts | Heat and Water | Needs ESP32 + sensor; one reading can't prove a blockage. |
| BreatheSafe: classroom air monitor | Air | Needs sensor + calibration. |
| LoopBack: waste contamination tracking | Waste and Energy | Classification common; impact hard to show in a weekend. |
| DropLedger: clip-on vibration leak sensor | Heat and Water | Hardware; overlaps Raat Reading. |
| CoolProof: do cooling centres help | Heat and Water | Too vague. |
| Kabadi Lens: scrap/e-waste price estimator | Waste and Energy | Good story; needs price data and test images. |
| Chhaon: cool-route finder | Heat and Water | Heat apps common; weak demo. |
| Corsi-Rosenthal kit planner | Air | Real impact; thin software. |

## Why Invisible Heat over JalDhwani

- Impact is the first judging criterion: heat deaths and lost work versus convenience.
- The central claim is a *finding* (invisible heat days), not only a feature.
- Lower technical risk: public formulas and public weather data versus uncertain phone acoustics.
- Missing piece: no physical device. If a physical element is wanted, add the **roadmap site-correction idea (F-34)**: a photo of a ₹150–300 thermometer-hygrometer, or a DIY black-globe thermometer (black-painted steel cup/ball with a probe thermometer) whose readings correct the forecast WBGT at the site. These are optional and not part of the weekend scope.

## Notes from a competing-track discussion

An earlier thread suggested Waste and Energy might have fewer visible entries. That was based on a weak public-search signal. Track-wise submission counts are not published. Do not use this in any pitch.

## Optional physical add-ons (roadmap only)

- On-site thermometer-hygrometer photo (read by Textract/Bedrock) to correct forecast.
- DIY black-globe thermometer for radiant heat.
- Phone-camera fingertip pulse check as heat-strain screening (clearly "screening, not diagnosis"). Not in scope; mention only as a future idea if at all.

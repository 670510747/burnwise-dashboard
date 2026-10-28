BurnWise — English UI update

Unzip these files into the existing repository root:
  app.py
  burnwise_policy.py
  english_ui.py
  requirements.txt
Keep the existing data/, assets/ and .streamlit/ folders.
All three Python files must be present beside one another.

The UI uses an offline English dictionary. No translation API or extra package is required.
Data processing, input paths, thresholds, raw status aliases and source CSV exports remain unchanged.
Subdistrict names and plot labels use English display text; source IDs remain unchanged in data and exports.
The redundant outer container around the three numbered story cards has been removed.
Simulated inputs and preliminary GISTDA comparison remain explicitly labelled.

Verification: six pages executed without exceptions using the existing supplied export fixture.
Simulation on/off, shortlist size, monthly filtering and sorting were exercised.
No remaining Thai display text was detected in those test paths.
No claim is made about untested future text or external basemap place-name tiles.
The English adapter wraps only display calls; raw processing and widget option values are retained.

Deployment: commit these files, then reboot the existing Streamlit app.
No deployment has been performed from this chat.

Slides: slides 14–15 use the latest user-supplied real screenshot. The screenshot predates the English/layout correction and is labelled accordingly. The browser security policy blocked capture of the local revised English app. Replace it with a new real capture after deployment.

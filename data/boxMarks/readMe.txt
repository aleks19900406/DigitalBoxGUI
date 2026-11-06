BOX MARKS - names of inputs, outputs, sliders ... for one test device
=====================================================================
Every box mark is one file  data/boxMarks/<any_name>.json  (the file name is shown in the BOX MARKS list).
You can create more box marks for different test devices: copy an existing .json and edit it.
Only the sections and indexes you need must be written, the others get default names.

Sections (index starts at 0):
  INPUT         0..31   input names
  OUTPUT        0..15   output names
  DIGITAL_POT   0..5    digital potentiometer names (only sliders with a name are shown)
  DAC_POT       0..7    dac table names
  READ_ADC      0..3
  SET_VOLTAGE   0..3
  READ_PWM1, READ_PWM2, SET_PWM1, SET_PWM2   0..1  (frequency, duty)
  SET_FREQ, SET_DUTY    one text
  AUTO1..AUTO4  name, input, output, mode (+ pulse_ms)
                mode = POSITIVE / NEGATIVE / PULSE
                PULSE: every time the input goes to True the output is switched ON and OFF again
                (pulse_ms = how long the output stays ON, default 1000)

Example:
{
  "INPUT": {"0": "PR1", "1": "FAN", "8": "PUMP"},
  "OUTPUT": {"0": "LOCK", "1": "DOOR", "6": "MEAR"},
  "DIGITAL_POT": {"0": "PT1000", "1": "MEAT"},
  "SET_FREQ": "SetFreq(Duty50%)",
  "AUTO1": {"name": "PYROLOCK", "input": 18, "output": 7, "mode": "PULSE", "pulse_ms": 1000}
}
A section can also be a list:  "OUTPUT": ["LOCK", "DOOR", "", "", "", "", "MEAR"]

LABELS  - text of any other button/label of the GUI: {"<object name of the widget>": "new text"}
          example: "LABELS": {"label_marks_4": "My heading"}

Renaming in the GUI: select the box marks, EDIT LAYOUT, double click a button/text (or select it and
press F2) and type the new text. It is saved in the json of the selected box marks (INPUT, OUTPUT, DIGITAL_POT,
READ_ADC, ... for their names, LABELS for everything else). An empty text returns the default name.

Old .txt box marks still work if there is no .json with the same name (the old files are in old_txt/).

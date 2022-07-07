# Schedule Generator
 Generate Schedules based on a csv of availabilities and a list of meetings with participants. Also generates alternate options for each date when possible. 

The UI is implemented in [Streamlit](https://streamlit.io)

## Requirements

- streamlit
- numpy
- pandas

## How does this thing work then?

create an environment where the requirements are installed, from within that environment run:

```python
streamlit run \path\to\ScheduleGenerator\ui.py
```

A page should open in your default browser showing the UI.

### The UI

A note on the terms used: Since this was created to generate theatre schedules, the terms 'actors' and 'scenes' are used instead of 'participant' and 'meeting'. This makes no difference to functionality.

There are 4 steps to generating a schedule. Each step is set in it's own expander (click on the + sign to show).

1. Import availabilities: 
   upload a csv. file in the format of the 'example_availabilities.csv' file included. (I used the export function of https://rallly.co)

2. Add new actors (participants):
   If needed, add new actors (or participants) manually, setting their availabilities. All the people in the availabilities csv are automatically imported.

3. Add Scenes (meetings):
   On the left column you can create scenes, and select the participants. You can also select participants whose presence is more important (such as the organizer, or lecturer). The importance of these people can be manually adjusted later. 
   On the right column you can delete all created scenes, and dowload /export & upload/import a json file containing the scenes.

4. Generate a schedule:
   In the first slider you can select the importance of the people marked as such in the scenes. This is a 1:1 scaling to other participants, so that an importance of 3 means that this person is the equivalent of 3 people joining. There is a preview of the weight of each participant per scene. 

   You can then select the scenes to be used in the generated schedule. This affects only the main schedule generated, not the alternate meetings. 
   Under 'Optimization' you can select the number of steps the optimization algorithm takes to find the best solution. 
   Clicking 'calculate' generates a schedule, giving it both as a list of strings separated by horizontal lines, and a downloadable csv with more details. 
   

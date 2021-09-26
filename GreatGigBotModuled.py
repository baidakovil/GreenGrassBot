#!/usr/bin/env python
# coding: utf-8

# In[1]:


import GreatGigBotLib

lastfmUser='ivanshello'
hoursDelta = 55
minListens = 3

events = GreatGigBotLib.getLastfmEvents(lastfmUser,hoursDelta,minListens)
GreatGigBotLib.prettyThree(events)


# -*- coding: utf-8 -*-
"""
Created on Wed Feb  9 23:38:20 2022

@author: Julian Latasa
"""

import datetime

from garminconnect import (
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

from garminconnect2 import (
    Garmin
)

import logging
logging.basicConfig(filename='garminerr.log', filemode='w', level=logging.DEBUG)

class SingletonGarmin:

    usuario = ''
    password = ''
    api = None
    connections = []
    date = None
    
    __instance = None
    @staticmethod    

    def getInstance():
      """ Static access method. """
      if SingletonGarmin.__instance == None:
         SingletonGarmin()
      return SingletonGarmin.__instance

    def __init__(self, usuario = None, password = None):
      """ Virtually private constructor. """
      if SingletonGarmin.__instance != None:
         raise Exception("This class is a singleton!")
      else:
         if (not(usuario is None) and not(password is None)):
             self.usuario = usuario
             self.password = password
         SingletonGarmin.__instance = self

    def setDate(self, date):
        self.date = date
    
    def getDate(self):
        return self.date
        
    def setConnections(self, connections):
        self.connections = connections
        
    def getConnections(self):
        return self.connections

    def setParams(self, usuario = None, password = None):
        if (not(usuario is None) and not(password is None)):
            self.usuario = usuario
            self.password = password

    def getParams(self):
        print(self.usuario)
        print(self.password)
        return (self.usuario + ' ' + self.password)

    def getApi(self):
        if (self.api is None):
            self.api = Garmin(self.usuario, self.password)
        return self.api

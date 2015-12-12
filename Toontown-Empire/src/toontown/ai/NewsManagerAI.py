from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.distributed.ClockDelta import globalClockDelta
from direct.task import Task
from otp.ai.MagicWordGlobal import magicWord
from otp.ai.MagicWordGlobal import CATEGORY_DEVELOPER
from toontown.effects.DistributedFireworkShowAI import DistributedFireworkShowAI
from toontown.effects import FireworkShows
from toontown.toonbase import ToontownGlobals
from toontown.parties import PartyGlobals
import HolidayGlobals
import datetime
import random

class NewsManagerAI(DistributedObjectAI):

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)
        self.activeHolidays = []
        self.fireworkTasks = []

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        self.__checkHolidays()
        self.checkTask = taskMgr.doMethodLater(15, self.__checkHolidays, 'holidayCheckTask')
        self.accept('avatarEntered', self.__handleAvatarEntered)

    def delete(self):
        DistributedObjectAI.delete(self)
        taskMgr.remove(self.checkTask)
        self.deleteFireworkTasks()

    def deleteFireworkTasks(self):
        if self.fireworkTasks:
            for task in self.fireworkTasks:
                taskMgr.remove(task)
            self.fireworkTasks = []

    def __handleAvatarEntered(self, av):
        avId = av.getDoId()

        if self.air.suitInvasionManager.getInvading():
            self.air.suitInvasionManager.notifyInvasionBulletin(avId)

        self.sendUpdateToAvatarId(avId, 'setActiveHolidays', [self.activeHolidays])

    def getActiveHolidays(self):
        return self.activeHolidays

    def __checkHolidays(self, task=None):
        date = datetime.datetime.now(HolidayGlobals.TIME_ZONE)

        for id in HolidayGlobals.Holidays:
            holiday = HolidayGlobals.Holidays[id]
            running = self.isHolidayRunning(id)

            if self.isHolidayInRange(holiday, date):
                if not running:
                    self.startHoliday(id)
            elif running:
                self.endHoliday(id)

        return Task.again

    def isHolidayInRange(self, holiday, date):
        if 'weekDay' in holiday:
            return holiday['weekDay'] == date.weekday()
        else:
            return HolidayGlobals.getStartDate(holiday) <= date <= HolidayGlobals.getEndDate(holiday)

    def isHolidayRunning(self, *args):
        return id in self.activeHolidays

    def startHoliday(self, id):
        if id in self.activeHolidays or id not in HolidayGlobals.Holidays:
            return

        self.activeHolidays.append(id)
        self.startSpecialHoliday(id)
        self.sendUpdate('startHoliday', [id])

    def endHoliday(self, id):
        if id not in self.activeHolidays or id not in HolidayGlobals.Holidays:
            return

        self.activeHolidays.remove(id)
        self.endSpecialHoliday(id)
        self.sendUpdate('endHoliday', [id])

    def startSpecialHoliday(self, id):
        if id == ToontownGlobals.FISH_BINGO or id == ToontownGlobals.SILLY_SATURDAY:
            messenger.send('checkBingoState')
        elif id in [ToontownGlobals.SUMMER_FIREWORKS, ToontownGlobals.NEW_YEAR_FIREWORKS]:
            self.fireworkTasks.append(taskMgr.doMethodLater((60 - datetime.datetime.now().minute) * 60, self.startFireworkTask, 'initialFireworkTask-{0}'.format(id, extraArgs=[id])))

    def endSpecialHoliday(self, id):
        if id == ToontownGlobals.FISH_BINGO or id == ToontownGlobals.SILLY_SATURDAY:
            messenger.send('checkBingoState')
        elif id in [ToontownGlobals.SUMMER_FIREWORKS, ToontownGlobals.NEW_YEAR_FIREWORKS]:
            self.deleteFireworkTasks()

    def startFireworkTask(self, id, task=None):
        self.startFireworks(id)
        self.fireworkTasks.append(taskMgr.doMethodLater(3600, self.startFireworks, 'fireworkTask-%s' % id, extraArgs=[id]))
        return Task.done

    def startFireworks(self, type, task=None):
        maxShow = len(FireworkShows.shows.get(type, [])) - 1

        for hood in self.air.hoods:
            if hood.zoneId == ToontownGlobals.GolfZone:
                continue

            fireworkShow = DistributedFireworkShowAI(self.air)
            fireworkShow.generateWithRequired(hood.zoneId)
            fireworkShow.b_startShow(type, random.randint(0, maxShow), globalClockDelta.getRealNetworkTime())

        return Task.again

    def isGrandPrixRunning(self):
        return self.isHolidayRunning(ToontownGlobals.SILLY_SATURDAY, ToontownGlobals.GRAND_PRIX) or True

@magicWord(category=CATEGORY_DEVELOPER)
def newsShutdown():
    """
    Shutdown the news manager tasks.
    """
    simbase.air.newsManager.deleteTasks()
    return 'News manager shut down!'

@magicWord(category=CATEGORY_DEVELOPER, types=[int])
def startHoliday(holiday):
    """
    Start a holiday.
    """
    if simbase.air.newsManager.startHoliday(holiday):
        return 'Started holiday {0}!'.format(holiday)
    
    return 'Holiday {0} is already running!'.format(holiday)

@magicWord(category=CATEGORY_DEVELOPER, types=[int])
def stopHoliday(holiday):
    """
    Stop a holiday.
    """
    if simbase.air.newsManager.endHoliday(holiday):
        return 'Stopped holiday {0}!'.format(holiday)
    
    return 'Holiday {0} is not running!'.format(holiday)
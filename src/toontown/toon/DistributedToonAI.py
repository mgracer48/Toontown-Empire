from direct.directnotify import DirectNotifyGlobal
from direct.distributed import DistributedSmoothNodeAI
from direct.distributed.ClockDelta import globalClockDelta
from direct.task import Task
from otp.ai.MagicWordGlobal import magicWord
from otp.ai.MagicWordGlobal import CATEGORY_TRIAL
from otp.ai.MagicWordGlobal import CATEGORY_STAFF
from otp.ai.MagicWordGlobal import CATEGORY_LEAD_STAFF
from direct.showbase.PythonUtil import union
from otp.ai.MagicWordGlobal import CATEGORY_DEVELOPER
from otp.ai.MagicWordGlobal import CATEGORY_LEADER
from otp.avatar import DistributedAvatarAI, DistributedPlayerAI
from otp.otpbase import OTPGlobals, OTPLocalizer
from toontown.battle import SuitBattleGlobals
from toontown.catalog import CatalogAccessoryItem, CatalogItem, CatalogItemList
from toontown.cogdominium import CogdoUtil
from toontown.chat import ResistanceChat
from toontown.coghq import CogDisguiseGlobals
from toontown.estate import FlowerBasket, FlowerCollection, GardenGlobals
from toontown.fishing import FishCollection, FishTank, FishGlobals
from toontown.golf import GolfGlobals
from toontown.hood import ZoneUtil
from toontown.parties import PartyGlobals
from toontown.parties.InviteInfo import InviteInfoBase
from toontown.parties.PartyGlobals import InviteStatus
from toontown.parties.PartyInfo import PartyInfoAI
from toontown.parties.PartyReplyInfo import PartyReplyInfoBase
from toontown.quest import QuestRewardCounter, Quests
from toontown.racing import RaceGlobals
from toontown.shtiker import CogPageGlobals
from toontown.suit import SuitDNA, SuitInvasionGlobals
from toontown.toon import NPCToons
from toontown.toonbase import TTLocalizer, ToontownBattleGlobals, ToontownGlobals
from NPCToons import npcFriends
import Experience, InventoryBase, ToonDNA, random, time
from toontown.uberdog import TopToonsGlobals
from otp.ai.MagicWordGlobal import spellbook
if simbase.wantPets:
    from toontown.pets import PetLookerAI, PetObserve
else:
    class PetLookerAI(object):
        pass

if simbase.wantKarts:
    from toontown.racing.KartDNA import KartDNA
    from toontown.racing.KartDNA import getNumFields


class DistributedToonAI(DistributedPlayerAI.DistributedPlayerAI,
                        DistributedSmoothNodeAI.DistributedSmoothNodeAI,
                        PetLookerAI.PetLookerAI):
    notify = DirectNotifyGlobal.directNotify.newCategory('DistributedToonAI')
    maxCallsPerNPC = 100
    partTypeIds = {ToontownGlobals.FT_FullSuit: (CogDisguiseGlobals.leftLegIndex,
                                                 CogDisguiseGlobals.rightLegIndex,
                                                 CogDisguiseGlobals.torsoIndex,
                                                 CogDisguiseGlobals.leftArmIndex,
                                                 CogDisguiseGlobals.rightArmIndex),
                   ToontownGlobals.FT_Leg: (CogDisguiseGlobals.leftLegIndex,
                                            CogDisguiseGlobals.rightLegIndex),
                   ToontownGlobals.FT_Arm: (CogDisguiseGlobals.leftArmIndex,
                                            CogDisguiseGlobals.rightArmIndex),
                   ToontownGlobals.FT_Torso: (CogDisguiseGlobals.torsoIndex,)}
    petId = None

    def __init__(self, air):
        DistributedPlayerAI.DistributedPlayerAI.__init__(self, air)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.__init__(self, air)

        if simbase.wantPets:
            PetLookerAI.PetLookerAI.__init__(self)

        self.air = air
        self.dna = ToonDNA.ToonDNA()
        self.inventory = None
        self.fishCollection = None
        self.fishTank = None
        self.experience = None
        self.petId = None
        self.quests = []
        self.cogs = []
        self.cogCounts = []
        self.NPCFriendsDict = {}
        self.clothesTopsList = []
        self.clothesBottomsList = []
        self.hatList = []
        self.glassesList = []
        self.backpackList = []
        self.shoesList = []
        self.hat = (0, 0, 0)
        self.glasses = (0, 0, 0)
        self.backpack = (0, 0, 0)
        self.shoes = (0, 0, 0)
        self.cogTypes = [0, 0, 0, 0]
        self.cogLevel = [0, 0, 0, 0]
        self.cogParts = [0, 0, 0, 0]
        self.cogRadar = [0, 0, 0, 0]
        self.cogIndex = -1
        self.disguisePageFlag = 0
        self.sosPageFlag = 0
        self.buildingRadar = [0, 0, 0, 0]
        self.fishingRod = 0
        self.fishingTrophies = []
        self.trackArray = []
        self.emoteAccess = [0] * 25
        self.maxMoney = 0
        self.maxBankMoney = 0
        self.bankMoney = 0
        self.gardenSpecials = []
        self.houseId = 0
        self.savedCheesyEffect = ToontownGlobals.CENormal
        self.savedCheesyHoodId = 0
        self.savedCheesyExpireTime = 0
        self.ghostMode = 0
        self.immortalMode = 0
        self.unlimitedGags = 0
        self.numPies = 0
        self.pieType = 0
        self._isGM = False
        self._gmType = None
        self.hpOwnedByBattle = 0
        if simbase.wantPets:
            self.petTrickPhrases = []
        if simbase.wantBingo:
            self.bingoCheat = False
        self.customMessages = []
        self.catalogNotify = ToontownGlobals.NoItems
        self.mailboxNotify = ToontownGlobals.NoItems
        self.catalogScheduleCurrentWeek = 0
        self.catalogScheduleNextTime = 0
        self.monthlyCatalog = CatalogItemList.CatalogItemList()
        self.weeklyCatalog = CatalogItemList.CatalogItemList()
        self.backCatalog = CatalogItemList.CatalogItemList()
        self.onOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization |
                                                       CatalogItem.DeliveryDate)
        self.onGiftOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.mailboxContents = CatalogItemList.CatalogItemList(store=CatalogItem.Customization)
        self.awardMailboxContents = CatalogItemList.CatalogItemList(store=CatalogItem.Customization)
        self.onAwardOrder = CatalogItemList.CatalogItemList(store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        self.kart = None
        if simbase.wantKarts:
            self.kartDNA = [-1] * getNumFields()
            self.tickets = 200
            self.allowSoloRace = False
            self.allowRaceTimeout = True
        self.setBattleId(0)
        self.gardenStarted = False
        self.flowerCollection = None
        self.shovel = 0
        self.shovelSkill = 0
        self.wateringCan = 0
        self.wateringCanSkill = 0
        self.hatePets = 1
        self.golfHistory = None
        self.golfHoleBest = None
        self.golfCourseBest = None
        self.unlimitedSwing = False
        self.numMailItems = 0
        self.simpleMailNotify = ToontownGlobals.NoItems
        self.inviteMailNotify = ToontownGlobals.NoItems
        self.invites = []
        self.hostedParties = []
        self.partiesInvitedTo = []
        self.partyReplyInfoBases = []
        self.teleportOverride = 0
        self.buffs = []
        self.redeemedCodes = []
        self.ignored = []
        self.reported = []
        self.trueFriends = []
        self.fishBingoTutorialDone = False
        self.nextKnockHeal = 0
        self.tfRequest = (0, 0)
        self.epp = []

    def generate(self):
        DistributedPlayerAI.DistributedPlayerAI.generate(self)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.generate(self)

    def announceGenerate(self):
        DistributedPlayerAI.DistributedPlayerAI.announceGenerate(self)
        DistributedSmoothNodeAI.DistributedSmoothNodeAI.announceGenerate(self)

        if self.isPlayerControlled():
            messenger.send('avatarEntered', [self])

        from toontown.toon.DistributedNPCToonBaseAI import DistributedNPCToonBaseAI
        if not isinstance(self, DistributedNPCToonBaseAI):
            self.sendUpdate('setDefaultShard', [self.air.districtId])

    def clearChat(self):
        self.sendUpdate('setTalk', ['.'])

    def setLocation(self, parentId, zoneId):
        DistributedPlayerAI.DistributedPlayerAI.setLocation(self, parentId, zoneId)

        from toontown.toon.DistributedNPCToonBaseAI import DistributedNPCToonBaseAI
        if not isinstance(self, DistributedNPCToonBaseAI):
            self.clearChat()

            if 100 <= zoneId < ToontownGlobals.DynamicZonesBegin:
                hood = ZoneUtil.getHoodId(zoneId)
                self.b_setLastHood(hood)
                self.b_setDefaultZone(hood)

                hoodsVisited = list(self.getHoodsVisited())
                if hood not in hoodsVisited:
                    hoodsVisited.append(hood)
                    self.b_setHoodsVisited(hoodsVisited)

                if zoneId == ToontownGlobals.GoofySpeedway or zoneId == ToontownGlobals.OutdoorZone:
                    tpAccess = self.getTeleportAccess()
                    if zoneId not in tpAccess:
                        tpAccess.append(zoneId)
                        self.b_setTeleportAccess(tpAccess)

    def sendDeleteEvent(self):
        if simbase.wantPets:
            isInEstate = self.isInEstate()
            wasInEstate = self.wasInEstate()
            if isInEstate or wasInEstate:
                PetObserve.send(self.estateZones, PetObserve.PetActionObserve(PetObserve.Actions.LOGOUT, self.doId))
                if wasInEstate:
                    self.cleanupEstateData()

        DistributedAvatarAI.DistributedAvatarAI.sendDeleteEvent(self)

    def delete(self):
        if self.isPlayerControlled():
            messenger.send('avatarExited', [self])
        if simbase.wantPets:
            if self.isInEstate():
                self.exitEstate()
            if self.zoneId != ToontownGlobals.QuietZone:
                self.announceZoneChange(ToontownGlobals.QuietZone, self.zoneId)
        taskName = self.uniqueName('cheesy-expires')
        taskMgr.remove(taskName)
        taskName = self.uniqueName('next-catalog')
        taskMgr.remove(taskName)
        taskName = self.uniqueName('next-delivery')
        taskMgr.remove(taskName)
        taskName = self.uniqueName('next-award-delivery')
        taskMgr.remove(taskName)
        taskName = 'next-bothDelivery-%s' % self.doId
        taskMgr.remove(taskName)
        self.stopToonUp()
        del self.dna
        if self.inventory:
            self.inventory.unload()
        del self.inventory
        del self.experience
        if simbase.wantPets:
            PetLookerAI.PetLookerAI.destroy(self)
        del self.kart
        self._sendExitServerEvent()

        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)
        DistributedPlayerAI.DistributedPlayerAI.delete(self)

    def deleteDummy(self):
        if self.inventory:
            self.inventory.unload()
        del self.inventory
        self.experience = None
        taskName = self.uniqueName('next-catalog')
        taskMgr.remove(taskName)

    def ban(self, comment):
        pass

    def disconnect(self):
        self.requestDelete()

    def patchDelete(self):
        del self.dna
        if self.inventory:
            self.inventory.unload()
        del self.inventory
        del self.experience
        if simbase.wantPets:
            PetLookerAI.PetLookerAI.destroy(self)
        self.doNotDeallocateChannel = True
        self.zoneId = None

        DistributedSmoothNodeAI.DistributedSmoothNodeAI.delete(self)
        DistributedPlayerAI.DistributedPlayerAI.delete(self)

    def handleLogicalZoneChange(self, newZoneId, oldZoneId):
        DistributedAvatarAI.DistributedAvatarAI.handleLogicalZoneChange(self, newZoneId, oldZoneId)

        if self.isPlayerControlled():
            messenger.send(self.staticGetLogicalZoneChangeAllEvent(), [newZoneId, oldZoneId, self])

    def announceZoneChange(self, newZoneId, oldZoneId):
        if simbase.wantPets:
            broadcastZones = [oldZoneId, newZoneId]
            if self.isInEstate() or self.wasInEstate():
                broadcastZones = union(broadcastZones, self.estateZones)
            PetObserve.send(broadcastZones, PetObserve.PetActionObserve(PetObserve.Actions.CHANGE_ZONE, self.doId, (oldZoneId, newZoneId)))

    def checkAccessorySanity(self, accessoryType, idx, textureIdx, colorIdx):
        if idx == 0 and textureIdx == 0 and colorIdx == 0:
            return 1
        if accessoryType == ToonDNA.HAT:
            stylesDict = ToonDNA.HatStyles
            accessoryTypeStr = 'Hat'
        elif accessoryType == ToonDNA.GLASSES:
            stylesDict = ToonDNA.GlassesStyles
            accessoryTypeStr = 'Glasses'
        elif accessoryType == ToonDNA.BACKPACK:
            stylesDict = ToonDNA.BackpackStyles
            accessoryTypeStr = 'Backpack'
        elif accessoryType == ToonDNA.SHOES:
            stylesDict = ToonDNA.ShoesStyles
            accessoryTypeStr = 'Shoes'
        else:
            return 0
        try:
            styleStr = stylesDict.keys()[stylesDict.values().index([idx, textureIdx, colorIdx])]
            accessoryItemId = 0
            for itemId in CatalogAccessoryItem.AccessoryTypes.keys():
                if styleStr == CatalogAccessoryItem.AccessoryTypes[itemId][CatalogAccessoryItem.ATString]:
                    accessoryItemId = itemId
                    break
            if accessoryItemId == 0:
                self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to wear invalid %s %d %d %d' % (accessoryTypeStr, idx, textureIdx, colorIdx))
                return 0
            return 1
        except:
            self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to wear invalid %s %d %d %d' % (accessoryTypeStr, idx, textureIdx, colorIdx))
            return 0

    def b_setHat(self, idx, textureIdx, colorIdx):
        self.d_setHat(idx, textureIdx, colorIdx)
        self.setHat(idx, textureIdx, colorIdx)

    def d_setHat(self, idx, textureIdx, colorIdx):
        if self.checkAccessorySanity(ToonDNA.HAT, idx, textureIdx, colorIdx):
            self.sendUpdate('setHat', [idx, textureIdx, colorIdx])

    def setHat(self, idx, textureIdx, colorIdx):
        if self.checkAccessorySanity(ToonDNA.HAT, idx, textureIdx, colorIdx):
            self.hat = (idx, textureIdx, colorIdx)

    def getHat(self):
        return self.hat

    def b_setGlasses(self, idx, textureIdx, colorIdx):
        self.d_setGlasses(idx, textureIdx, colorIdx)
        self.setGlasses(idx, textureIdx, colorIdx)

    def d_setGlasses(self, idx, textureIdx, colorIdx):
        if self.checkAccessorySanity(ToonDNA.GLASSES, idx, textureIdx, colorIdx):
            self.sendUpdate('setGlasses', [idx, textureIdx, colorIdx])

    def setGlasses(self, idx, textureIdx, colorIdx):
        if self.checkAccessorySanity(ToonDNA.GLASSES, idx, textureIdx, colorIdx):
            self.glasses = (idx, textureIdx, colorIdx)

    def getGlasses(self):
        return self.glasses

    def b_setBackpack(self, idx, textureIdx, colorIdx):
        self.d_setBackpack(idx, textureIdx, colorIdx)
        self.setBackpack(idx, textureIdx, colorIdx)

    def d_setBackpack(self, idx, textureIdx, colorIdx):
        if self.checkAccessorySanity(ToonDNA.BACKPACK, idx, textureIdx, colorIdx):
            self.sendUpdate('setBackpack', [idx, textureIdx, colorIdx])

    def setBackpack(self, idx, textureIdx, colorIdx):
        if self.checkAccessorySanity(ToonDNA.BACKPACK, idx, textureIdx, colorIdx):
            self.backpack = (idx, textureIdx, colorIdx)

    def getBackpack(self):
        return self.backpack

    def b_setShoes(self, idx, textureIdx, colorIdx):
        self.d_setShoes(idx, textureIdx, colorIdx)
        self.setShoes(idx, textureIdx, colorIdx)

    def d_setShoes(self, idx, textureIdx, colorIdx):
        if self.checkAccessorySanity(ToonDNA.SHOES, idx, textureIdx, colorIdx):
            self.sendUpdate('setShoes', [idx, textureIdx, colorIdx])

    def setShoes(self, idx, textureIdx, colorIdx):
        if self.checkAccessorySanity(ToonDNA.SHOES, idx, textureIdx, colorIdx):
            self.shoes = (idx, textureIdx, colorIdx)

    def getShoes(self):
        return self.shoes

    def b_setDNAString(self, string):
        self.d_setDNAString(string)
        self.setDNAString(string)

    def d_setDNAString(self, string):
        self.sendUpdate('setDNAString', [string])

    def setDNAString(self, string):
        self.dna.makeFromNetString(string)
        if not self.verifyDNA():
            self.notify.warning('Avatar %d has an invalid DNA string.' % self.doId)
            self.air.writeServerEvent(
                'suspicious', self.doId, 'Invalid DNA string.')

    @staticmethod
    def verifyDNA():
        return True

    def getDNAString(self):
        return self.dna.makeNetString()

    def getStyle(self):
        return self.dna

    def b_setExperience(self, experience):
        self.d_setExperience(experience)
        self.setExperience(experience)

    def d_setExperience(self, experience):
        self.sendUpdate('setExperience', [experience])

    def setExperience(self, experience):
        self.experience = Experience.Experience(experience, self)

    def getExperience(self):
        return self.experience.makeNetString()

    def b_setIgnored(self, ignored):
        self.d_setIgnored(ignored)
        self.setIgnored(ignored)

    def d_setIgnored(self, ignored):
        self.sendUpdate('setIgnored', [ignored])

    def setIgnored(self, ignored):
        self.ignored = ignored

    def getIgnored(self):
        return self.ignored

    def setReported(self, reported):
        self.reported = reported

    def getReported(self):
        return self.reported

    def isReported(self, doId):
        return doId in self.reported

    def b_setInventory(self, inventory):
        self.setInventory(inventory)
        self.d_setInventory(self.getInventory())

    def d_setInventory(self, inventory):
        self.sendUpdate('setInventory', [inventory])

    def setInventory(self, inventoryNetString):
        if self.inventory:
            self.inventory.updateInvString(inventoryNetString)
        else:
            self.inventory = InventoryBase.InventoryBase(self, inventoryNetString)
        emptyInv = InventoryBase.InventoryBase(self)
        emptyString = emptyInv.makeNetString()
        lengthMatch = len(inventoryNetString) - len(emptyString)
        if lengthMatch != 0:
            if len(inventoryNetString) == 42:
                oldTracks = 7
                oldLevels = 6
            elif len(inventoryNetString) == 49:
                oldTracks = 7
                oldLevels = 7
            else:
                oldTracks = 0
                oldLevels = 0
            if oldTracks == 0 and oldLevels == 0:
                self.notify.warning('reseting invalid inventory to MAX on toon: %s' % self.doId)
                self.inventory.zeroInv()
                self.inventory.maxOutInv(1)
            else:
                newInventory = InventoryBase.InventoryBase(self)
                oldList = emptyInv.makeFromNetStringForceSize(inventoryNetString, oldTracks, oldLevels)
                for indexTrack in xrange(0, oldTracks):
                    for indexGag in xrange(0, oldLevels):
                        newInventory.addItems(indexTrack, indexGag, oldList[indexTrack][indexGag])
                self.inventory.unload()
                self.inventory = newInventory
            self.d_setInventory(self.getInventory())

    def getInventory(self):
        return self.inventory.makeNetString()

    def doRestock(self, noUber = 1):
        self.inventory.zeroInv()
        self.inventory.maxOutInv(noUber)
        self.d_setInventory(self.inventory.makeNetString())

    def setDefaultShard(self, shard):
        self.defaultShard = shard

    def getDefaultShard(self):
        return self.defaultShard

    def setDefaultZone(self, zone):
        self.defaultZone = zone

    def d_setDefaultZone(self, zone):
        self.sendUpdate('setDefaultZone', [zone])

    def b_setDefaultZone(self, zone):
        if zone != self.defaultZone:
            self.setDefaultZone(zone)
            self.d_setDefaultZone(zone)

    def getDefaultZone(self):
        return self.defaultZone

    def d_setFriendsList(self, friendsList):
        self.sendUpdate('setFriendsList', [friendsList])

    def setFriendsList(self, friendsList):
        self.friendsList = friendsList

    def getFriendsList(self):
        return self.friendsList

    def extendFriendsList(self, friendId):
        if friendId in self.friendsList:
            return

        self.friendsList.append(friendId)
        self.air.questManager.toonMadeFriend(self)

    def getBattleId(self):
        if self.battleId >= 0:
            return self.battleId
        else:
            return 0

    def b_setBattleId(self, battleId):
        self.setBattleId(battleId)
        self.d_setBattleId(battleId)

    def d_setBattleId(self, battleId):
        if self.battleId >= 0:
            self.sendUpdate('setBattleId', [battleId])
        else:
            self.sendUpdate('setBattleId', [0])

    def setBattleId(self, battleId):
        self.battleId = battleId

    def d_setNPCFriendsDict(self, NPCFriendsDict):
        NPCFriendsList = []
        for friend in NPCFriendsDict.keys():
            NPCFriendsList.append((friend, NPCFriendsDict[friend]))

        self.sendUpdate('setNPCFriendsDict', [NPCFriendsList])

    def setNPCFriendsDict(self, NPCFriendsList):
        self.NPCFriendsDict = {}
        for friendPair in NPCFriendsList:
            self.NPCFriendsDict[friendPair[0]] = friendPair[1]

    def getNPCFriendsDict(self):
        return self.NPCFriendsDict

    def b_setNPCFriendsDict(self, NPCFriendsList):
        self.setNPCFriendsDict(NPCFriendsList)
        self.d_setNPCFriendsDict(self.NPCFriendsDict)

    def resetNPCFriendsDict(self):
        self.b_setNPCFriendsDict([])

    def attemptAddNPCFriend(self, npcFriend, method=Quests.WithCheat):
        numCalls = simbase.air.config.GetInt('sos-card-reward', 1)

        if numCalls <= 0:
            self.notify.warning('invalid numCalls: %d' % numCalls)
            return 0
        if npcFriend in self.NPCFriendsDict:
            self.NPCFriendsDict[npcFriend] += numCalls
        elif npcFriend in npcFriends:
            self.NPCFriendsDict[npcFriend] = numCalls
        else:
            self.notify.warning('invalid NPC: %d' % npcFriend)
            return 0
        if self.NPCFriendsDict[npcFriend] > self.maxCallsPerNPC:
            self.NPCFriendsDict[npcFriend] = self.maxCallsPerNPC
        self.d_setNPCFriendsDict(self.NPCFriendsDict)
        self.air.questManager.toonMadeNPCFriend(self, numCalls, method)
        return 1

    def attemptSubtractNPCFriend(self, npcFriend):
        if npcFriend not in self.NPCFriendsDict:
            self.notify.warning('attemptSubtractNPCFriend: invalid NPC %s' % npcFriend)
            return 0
        if hasattr(self, 'autoRestockSOS') and self.autoRestockSOS:
            cost = 0
        else:
            cost = 1
        self.NPCFriendsDict[npcFriend] -= cost
        if self.NPCFriendsDict[npcFriend] <= 0:
            del self.NPCFriendsDict[npcFriend]
        self.d_setNPCFriendsDict(self.NPCFriendsDict)
        return 1

    def restockAllNPCFriends(self):
        desiredNpcFriends = [2001, 2011, 3112, 4119, 1116, 3137, 3135]
        self.resetNPCFriendsDict()
        for npcId in desiredNpcFriends:
            self.attemptAddNPCFriend(npcId)

    def isTrunkFull(self, extraAccessories = 0):
        numAccessories = (len(self.hatList) + len(self.glassesList) + len(self.backpackList) + len(self.shoesList)) / 3
        return numAccessories + extraAccessories >= ToontownGlobals.MaxAccessories

    def d_setHatList(self, clothesList):
        self.sendUpdate('setHatList', [clothesList])

    def setHatList(self, clothesList):
        self.hatList = clothesList

    def b_setHatList(self, clothesList):
        self.setHatList(clothesList)
        self.d_setHatList(clothesList)

    def getHatList(self):
        return self.hatList

    def d_setGlassesList(self, clothesList):
        self.sendUpdate('setGlassesList', [clothesList])

    def setGlassesList(self, clothesList):
        self.glassesList = clothesList

    def b_setGlassesList(self, clothesList):
        self.setGlassesList(clothesList)
        self.d_setGlassesList(clothesList)

    def getGlassesList(self):
        return self.glassesList

    def d_setBackpackList(self, clothesList):
        self.sendUpdate('setBackpackList', [clothesList])

    def setBackpackList(self, clothesList):
        self.backpackList = clothesList

    def b_setBackpackList(self, clothesList):
        self.setBackpackList(clothesList)
        self.d_setBackpackList(clothesList)

    def getBackpackList(self):
        return self.backpackList

    def d_setShoesList(self, clothesList):
        self.sendUpdate('setShoesList', [clothesList])
        return None

    def setShoesList(self, clothesList):
        self.shoesList = clothesList

    def b_setShoesList(self, clothesList):
        self.setShoesList(clothesList)
        self.d_setShoesList(clothesList)

    def getShoesList(self):
        return self.shoesList

    def addToAccessoriesList(self, accessoryType, geomIdx, texIdx, colorIdx):
        if self.isTrunkFull():
            return 0
        if accessoryType == ToonDNA.HAT:
            itemList = self.hatList
        elif accessoryType == ToonDNA.GLASSES:
            itemList = self.glassesList
        elif accessoryType == ToonDNA.BACKPACK:
            itemList = self.backpackList
        elif accessoryType == ToonDNA.SHOES:
            itemList = self.shoesList
        else:
            return 0
        index = 0
        for i in xrange(0, len(itemList), 3):
            if itemList[i] == geomIdx and itemList[i + 1] == texIdx and itemList[i + 2] == colorIdx:
                return 0

        if accessoryType == ToonDNA.HAT:
            self.hatList.append(geomIdx)
            self.hatList.append(texIdx)
            self.hatList.append(colorIdx)
        elif accessoryType == ToonDNA.GLASSES:
            self.glassesList.append(geomIdx)
            self.glassesList.append(texIdx)
            self.glassesList.append(colorIdx)
        elif accessoryType == ToonDNA.BACKPACK:
            self.backpackList.append(geomIdx)
            self.backpackList.append(texIdx)
            self.backpackList.append(colorIdx)
        elif accessoryType == ToonDNA.SHOES:
            self.shoesList.append(geomIdx)
            self.shoesList.append(texIdx)
            self.shoesList.append(colorIdx)
        return 1

    def replaceItemInAccessoriesList(self, accessoryType, geomIdxA, texIdxA, colorIdxA, geomIdxB, texIdxB, colorIdxB):
        if accessoryType == ToonDNA.HAT:
            itemList = self.hatList
        elif accessoryType == ToonDNA.GLASSES:
            itemList = self.glassesList
        elif accessoryType == ToonDNA.BACKPACK:
            itemList = self.backpackList
        elif accessoryType == ToonDNA.SHOES:
            itemList = self.shoesList
        else:
            return 0
        index = 0
        for i in xrange(0, len(itemList), 3):
            if itemList[i] == geomIdxA and itemList[i + 1] == texIdxA and itemList[i + 2] == colorIdxA:
                if accessoryType == ToonDNA.HAT:
                    self.hatList[i] = geomIdxB
                    self.hatList[i + 1] = texIdxB
                    self.hatList[i + 2] = colorIdxB
                elif accessoryType == ToonDNA.GLASSES:
                    self.glassesList[i] = geomIdxB
                    self.glassesList[i + 1] = texIdxB
                    self.glassesList[i + 2] = colorIdxB
                elif accessoryType == ToonDNA.BACKPACK:
                    self.backpackList[i] = geomIdxB
                    self.backpackList[i + 1] = texIdxB
                    self.backpackList[i + 2] = colorIdxB
                else:
                    self.shoesList[i] = geomIdxB
                    self.shoesList[i + 1] = texIdxB
                    self.shoesList[i + 2] = colorIdxB
                return 1

        return 0

    def hasAccessory(self, accessoryType, geomIdx, texIdx, colorIdx):
        if accessoryType == ToonDNA.HAT:
            itemList = self.hatList
            cur = self.hat
        elif accessoryType == ToonDNA.GLASSES:
            itemList = self.glassesList
            cur = self.glasses
        elif accessoryType == ToonDNA.BACKPACK:
            itemList = self.backpackList
            cur = self.backpack
        elif accessoryType == ToonDNA.SHOES:
            itemList = self.shoesList
            cur = self.shoes
        else:
            raise 'invalid accessory type %s' % accessoryType
        if cur == (geomIdx, texIdx, colorIdx):
            return True
        for i in xrange(0, len(itemList), 3):
            if itemList[i] == geomIdx and itemList[i + 1] == texIdx and itemList[i + 2] == colorIdx:
                return True

        return False

    def isValidAccessorySetting(self, accessoryType, geomIdx, texIdx, colorIdx):
        if not geomIdx and not texIdx and not colorIdx:
            return True
        return self.hasAccessory(accessoryType, geomIdx, texIdx, colorIdx)

    def removeItemInAccessoriesList(self, accessoryType, geomIdx, texIdx, colorIdx):
        if accessoryType == ToonDNA.HAT:
            itemList = self.hatList
        elif accessoryType == ToonDNA.GLASSES:
            itemList = self.glassesList
        elif accessoryType == ToonDNA.BACKPACK:
            itemList = self.backpackList
        elif accessoryType == ToonDNA.SHOES:
            itemList = self.shoesList
        else:
            return 0
        listLen = len(itemList)
        if listLen < 3:
            self.notify.warning('Accessory list is not long enough to delete anything')
            return 0
        index = 0
        for i in xrange(0, len(itemList), 3):
            if itemList[i] == geomIdx and itemList[i + 1] == texIdx and itemList[i + 2] == colorIdx:
                itemList = itemList[0:i] + itemList[i + 3:listLen]
                if accessoryType == ToonDNA.HAT:
                    self.hatList = itemList[:]
                    styles = ToonDNA.HatStyles
                    descDict = TTLocalizer.HatStylesDescriptions
                elif accessoryType == ToonDNA.GLASSES:
                    self.glassesList = itemList[:]
                    styles = ToonDNA.GlassesStyles
                    descDict = TTLocalizer.GlassesStylesDescriptions
                elif accessoryType == ToonDNA.BACKPACK:
                    self.backpackList = itemList[:]
                    styles = ToonDNA.BackpackStyles
                    descDict = TTLocalizer.BackpackStylesDescriptions
                elif accessoryType == ToonDNA.SHOES:
                    self.shoesList = itemList[:]
                    styles = ToonDNA.ShoesStyles
                    descDict = TTLocalizer.ShoesStylesDescriptions
                styleName = 'none'
                for style in styles.items():
                    if style[1] == [geomIdx, texIdx, colorIdx]:
                        styleName = style[0]
                        break

                if styleName == 'none' or styleName not in descDict:
                    self.air.writeServerEvent('suspicious', self.doId, ' tried to remove wrong accessory code %d %d %d' % (geomIdx, texIdx, colorIdx))
                else:
                    self.air.writeServerEvent('accessory', self.doId, ' removed accessory %s' % descDict[styleName])
                return 1

        return 0

    def d_setMaxClothes(self, max):
        self.sendUpdate('setMaxClothes', [self.maxClothes])

    def setMaxClothes(self, max):
        self.maxClothes = max

    def b_setMaxClothes(self, max):
        self.setMaxClothes(max)
        self.d_setMaxClothes(max)

    def getMaxClothes(self):
        return self.maxClothes

    def isClosetFull(self, extraClothes = 0):
        numClothes = len(self.clothesTopsList) / 4 + len(self.clothesBottomsList) / 2
        return numClothes + extraClothes >= self.maxClothes

    def d_setClothesTopsList(self, clothesList):
        self.sendUpdate('setClothesTopsList', [clothesList])

    def setClothesTopsList(self, clothesList):
        self.clothesTopsList = clothesList

    def b_setClothesTopsList(self, clothesList):
        self.setClothesTopsList(clothesList)
        self.d_setClothesTopsList(clothesList)

    def getClothesTopsList(self):
        return self.clothesTopsList

    def addToClothesTopsList(self, topTex, topTexColor, sleeveTex, sleeveTexColor):
        if self.isClosetFull(1):
            return 0
        index = 0
        for i in xrange(0, len(self.clothesTopsList), 4):
            if self.clothesTopsList[i] == topTex and self.clothesTopsList[i + 1] == topTexColor and self.clothesTopsList[i + 2] == sleeveTex and self.clothesTopsList[i + 3] == sleeveTexColor:
                return 0

        self.clothesTopsList.append(topTex)
        self.clothesTopsList.append(topTexColor)
        self.clothesTopsList.append(sleeveTex)
        self.clothesTopsList.append(sleeveTexColor)
        return 1

    def replaceItemInClothesTopsList(self, topTexA, topTexColorA, sleeveTexA, sleeveTexColorA, topTexB, topTexColorB, sleeveTexB, sleeveTexColorB):
        index = 0
        for i in xrange(0, len(self.clothesTopsList), 4):
            if self.clothesTopsList[i] == topTexA and self.clothesTopsList[i + 1] == topTexColorA and self.clothesTopsList[i + 2] == sleeveTexA and self.clothesTopsList[i + 3] == sleeveTexColorA:
                self.clothesTopsList[i] = topTexB
                self.clothesTopsList[i + 1] = topTexColorB
                self.clothesTopsList[i + 2] = sleeveTexB
                self.clothesTopsList[i + 3] = sleeveTexColorB
                return 1

        return 0

    def removeItemInClothesTopsList(self, topTex, topTexColor, sleeveTex, sleeveTexColor):
        listLen = len(self.clothesTopsList)
        if listLen < 4:
            self.notify.warning('Clothes top list is not long enough to delete anything')
            return 0
        index = 0
        for i in xrange(0, listLen, 4):
            if self.clothesTopsList[i] == topTex and self.clothesTopsList[i + 1] == topTexColor and self.clothesTopsList[i + 2] == sleeveTex and self.clothesTopsList[i + 3] == sleeveTexColor:
                self.clothesTopsList = self.clothesTopsList[0:i] + self.clothesTopsList[i + 4:listLen]
                return 1

        return 0

    def d_setClothesBottomsList(self, clothesList):
        self.sendUpdate('setClothesBottomsList', [clothesList])

    def setClothesBottomsList(self, clothesList):
        self.clothesBottomsList = clothesList

    def b_setClothesBottomsList(self, clothesList):
        self.setClothesBottomsList(clothesList)
        self.d_setClothesBottomsList(clothesList)

    def getClothesBottomsList(self):
        return self.clothesBottomsList

    def addToClothesBottomsList(self, botTex, botTexColor):
        if self.isClosetFull(1):
            self.notify.warning('clothes bottoms list is full')
            return 0
        index = 0
        for i in xrange(0, len(self.clothesBottomsList), 2):
            if self.clothesBottomsList[i] == botTex and self.clothesBottomsList[i + 1] == botTexColor:
                return 0

        self.clothesBottomsList.append(botTex)
        self.clothesBottomsList.append(botTexColor)
        return 1

    def replaceItemInClothesBottomsList(self, botTexA, botTexColorA, botTexB, botTexColorB):
        index = 0
        for i in xrange(0, len(self.clothesBottomsList), 2):
            if self.clothesBottomsList[i] == botTexA and self.clothesBottomsList[i + 1] == botTexColorA:
                self.clothesBottomsList[i] = botTexB
                self.clothesBottomsList[i + 1] = botTexColorB
                return 1

        return 0

    def removeItemInClothesBottomsList(self, botTex, botTexColor):
        listLen = len(self.clothesBottomsList)
        if listLen < 2:
            self.notify.warning('Clothes bottoms list is not long enough to delete anything')
            return 0
        index = 0
        for i in xrange(0, len(self.clothesBottomsList), 2):
            if self.clothesBottomsList[i] == botTex and self.clothesBottomsList[i + 1] == botTexColor:
                self.clothesBottomsList = self.clothesBottomsList[0:i] + self.clothesBottomsList[i + 2:listLen]
                return 1

        return 0

    def d_catalogGenClothes(self):
        self.sendUpdate('catalogGenClothes', [self.doId])

    def d_catalogGenAccessories(self):
        self.sendUpdate('catalogGenAccessories', [self.doId])

    def takeDamage(self, hpLost, quietly = 0, sendTotal = 1):
        if not self.immortalMode:
            if not quietly:
                self.sendUpdate('takeDamage', [hpLost])
            if hpLost > 0 and self.hp > 0:
                self.hp -= hpLost
                if self.hp <= 0:
                    self.hp = -1
        if not self.hpOwnedByBattle:
            self.hp = min(self.hp, self.maxHp)
            if sendTotal:
                self.d_setHp(self.hp)

    def b_setMaxHp(self, maxHp):
        if self.maxHp == maxHp:
            return

        if (maxHp > ToontownGlobals.MaxHpLimit):
            self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to go over the HP limit.')
            self.d_setMaxHp(ToontownGlobals.MaxHpLimit)
            self.setMaxHp(ToontownGlobals.MaxHpLimit)
        else:
            self.d_setMaxHp(maxHp)
            self.setMaxHp(maxHp)

    def d_setMaxHp(self, maxHp):
        self.sendUpdate('setMaxHp', [maxHp])

    def b_setTutorialAck(self, tutorialAck):
        self.d_setTutorialAck(tutorialAck)
        self.setTutorialAck(tutorialAck)

    def d_setTutorialAck(self, tutorialAck):
        self.sendUpdate('setTutorialAck', [tutorialAck])

    def setTutorialAck(self, tutorialAck):
        self.tutorialAck = tutorialAck

    def getTutorialAck(self):
        return self.tutorialAck

    def d_setEarnedExperience(self, earnedExp):
        self.sendUpdate('setEarnedExperience', [earnedExp])

    def setHoodsVisited(self, hoods):
        self.hoodsVisited = hoods
        self.notify.debug('setting hood zone list to %s' % self.hoodsVisited)

    def getHoodsVisited(self):
        return self.hoodsVisited

    def setLastHood(self, hood):
        self.lastHood = hood

    def d_setLastHood(self, hood):
        self.sendUpdate('setLastHood', [hood])

    def b_setLastHood(self, hood):
        if hood != self.lastHood:
            self.setLastHood(hood)
            self.d_setLastHood(hood)

    def getLastHood(self):
        return self.lastHood

    def b_setAnimState(self, animName, animMultiplier):
        self.setAnimState(animName, animMultiplier)
        self.d_setAnimState(animName, animMultiplier)

    def d_setAnimState(self, animName, animMultiplier):
        timestamp = globalClockDelta.getRealNetworkTime()
        self.sendUpdate('setAnimState', [animName, animMultiplier, timestamp])
        return None

    def setAnimState(self, animName, animMultiplier, timestamp = 0):
        if animName not in ToontownGlobals.ToonAnimStates:
            desc = 'tried to set invalid animState: %s' % (animName,)
            if config.GetBool('want-ban-animstate', 1):
                #simbase.air.banManager.ban(self.doId, self.DISLid, desc)
                pass
            else:
                self.air.writeServerEvent('suspicious', self.doId, desc)
            return
        self.animName = animName
        self.animMultiplier = animMultiplier

    def b_setCogStatus(self, cogStatusList):
        self.setCogStatus(cogStatusList)
        self.d_setCogStatus(cogStatusList)

    def setCogStatus(self, cogStatusList):
        self.notify.debug('setting cogs to %s' % cogStatusList)
        self.cogs = cogStatusList

    def d_setCogStatus(self, cogStatusList):
        self.sendUpdate('setCogStatus', [cogStatusList])

    def getCogStatus(self):
        return self.cogs

    def b_setCogCount(self, cogCountList):
        self.setCogCount(cogCountList)
        self.d_setCogCount(cogCountList)

    def setCogCount(self, cogCountList):
        self.notify.debug('setting cogCounts to %s' % cogCountList)
        self.cogCounts = cogCountList

    def d_setCogCount(self, cogCountList):
        self.sendUpdate('setCogCount', [cogCountList])

    def getCogCount(self):
        return self.cogCounts

    def b_setCogRadar(self, radar):
        self.setCogRadar(radar)
        self.d_setCogRadar(radar)

    def setCogRadar(self, radar):
        if not radar:
            self.notify.warning('cogRadar set to bad value: %s. Resetting to [0,0,0,0]' % radar)
            self.cogRadar = [0,
                             0,
                             0,
                             0]
        else:
            self.cogRadar = radar

    def d_setCogRadar(self, radar):
        self.sendUpdate('setCogRadar', [radar])

    def getCogRadar(self):
        return self.cogRadar

    def b_setBuildingRadar(self, radar):
        self.setBuildingRadar(radar)
        self.d_setBuildingRadar(radar)

    def setBuildingRadar(self, radar):
        if not radar:
            self.notify.warning('buildingRadar set to bad value: %s. Resetting to [0,0,0,0]' % radar)
            self.buildingRadar = [0,
                                  0,
                                  0,
                                  0]
        else:
            self.buildingRadar = radar

    def d_setBuildingRadar(self, radar):
        self.sendUpdate('setBuildingRadar', [radar])

    def getBuildingRadar(self):
        return self.buildingRadar

    def b_setCogTypes(self, types):
        self.setCogTypes(types)
        self.d_setCogTypes(types)

    def setCogTypes(self, types):
        if not types:
            self.notify.warning('cogTypes set to bad value: %s. Resetting to [0,0,0,0]' % types)
            self.cogTypes = [0,
             0,
             0,
             0]
        else:
            for i in xrange(len(types)):
                if types[i] == SuitDNA.suitsPerDept - 1:
                    zoneId = SuitDNA.suitDeptZones[i]
                    tpAccess = self.getTeleportAccess()

                    if zoneId not in tpAccess:
                        tpAccess.append(zoneId)
                        self.b_setTeleportAccess(tpAccess)
            self.cogTypes = types

    def d_setCogTypes(self, types):
        self.sendUpdate('setCogTypes', [types])

    def getCogTypes(self):
        return self.cogTypes

    def b_setCogLevels(self, levels):
        self.setCogLevels(levels)
        self.d_setCogLevels(levels)

    def setCogLevels(self, levels):
        if not levels:
            self.notify.warning('cogLevels set to bad value: %s. Resetting to [0,0,0,0]' % levels)
            self.cogLevels = [0,
                              0,
                              0,
                              0]
        else:
            self.cogLevels = levels

    def d_setCogLevels(self, levels):
        self.sendUpdate('setCogLevels', [levels])

    def getCogLevels(self):
        return self.cogLevels

    def incCogLevel(self, dept):
        newLevel = self.cogLevels[dept] + 1
        cogTypeStr = SuitDNA.suitHeadTypes[self.cogTypes[dept]]
        lastCog = self.cogTypes[dept] >= SuitDNA.suitsPerDept - 1
        if not lastCog:
            maxLevel = SuitBattleGlobals.SuitAttributes[cogTypeStr]['level'] + 4
        else:
            maxLevel = ToontownGlobals.MaxCogSuitLevel
        if newLevel > maxLevel:
            if not lastCog:
                self.cogTypes[dept] += 1
                self.d_setCogTypes(self.cogTypes)
                cogTypeStr = SuitDNA.suitHeadTypes[self.cogTypes[dept]]
                self.cogLevels[dept] = SuitBattleGlobals.SuitAttributes[cogTypeStr]['level']
                self.d_setCogLevels(self.cogLevels)
        else:
            self.cogLevels[dept] += 1
            self.d_setCogLevels(self.cogLevels)
            if lastCog:
                if self.cogLevels[dept] in ToontownGlobals.CogSuitHPLevels:
                    maxHp = self.getMaxHp()
                    maxHp = min(ToontownGlobals.MaxHpLimit, maxHp + 1)
                    self.b_setMaxHp(maxHp)
                    self.toonUp(maxHp)
        self.air.writeServerEvent('cogSuit', self.doId, '%s|%s|%s' % (dept, self.cogTypes[dept], self.cogLevels[dept]))

    def getNumPromotions(self, dept):
        if dept not in SuitDNA.suitDepts:
            self.notify.warning('getNumPromotions: Invalid parameter dept=%s' % dept)
            return 0
        deptIndex = SuitDNA.suitDepts.index(dept)
        cogType = self.cogTypes[deptIndex]
        cogTypeStr = SuitDNA.suitHeadTypes[cogType]
        lowestCogLevel = SuitBattleGlobals.SuitAttributes[cogTypeStr]['level']
        multiple = 5 * cogType
        additional = self.cogLevels[deptIndex] - lowestCogLevel
        numPromotions = multiple + additional
        return numPromotions

    def b_setCogParts(self, parts):
        self.setCogParts(parts)
        self.d_setCogParts(parts)

    def setCogParts(self, parts):
        if not parts:
            self.notify.warning('cogParts set to bad value: %s. Resetting to [0,0,0,0]' % parts)
            self.cogParts = [0,
                             0,
                             0,
                             0]
        else:
            self.cogParts = parts

    def d_setCogParts(self, parts):
        self.sendUpdate('setCogParts', [parts])

    def getCogParts(self):
        return self.cogParts

    def giveCogPart(self, part, dept):
        dept = CogDisguiseGlobals.dept2deptIndex(dept)
        parts = self.getCogParts()
        parts[dept] = parts[dept] | part
        self.b_setCogParts(parts)

    def hasCogPart(self, part, dept):
        dept = CogDisguiseGlobals.dept2deptIndex(dept)
        if self.cogParts[dept] & part:
            return 1
        else:
            return 0

    def giveGenericCogPart(self, factoryType, dept):
        for partTypeId in self.partTypeIds[factoryType]:
            nextPart = CogDisguiseGlobals.getNextPart(self.getCogParts(), partTypeId, dept)
            if nextPart:
                break
        if nextPart:
            self.giveCogPart(nextPart, dept)
            return nextPart

    def takeCogPart(self, part, dept):
        dept = CogDisguiseGlobals.dept2deptIndex(dept)
        parts = self.getCogParts()
        if parts[dept] & part:
            parts[dept] = parts[dept] ^ part
            self.b_setCogParts(parts)

    def loseCogParts(self, dept):
        loseCount = random.randrange(CogDisguiseGlobals.MinPartLoss, CogDisguiseGlobals.MaxPartLoss + 1)
        parts = self.getCogParts()
        partBitmask = parts[dept]
        partList = xrange(17)
        while loseCount > 0 and partList:
            losePart = random.choice(partList)
            partList.remove(losePart)
            losePartBit = 1 << losePart
            if partBitmask & losePartBit:
                partBitmask &= ~losePartBit
                loseCount -= 1

        parts[dept] = partBitmask
        self.b_setCogParts(parts)

    def b_setCogMerits(self, merits):
        self.setCogMerits(merits)
        self.d_setCogMerits(merits)

    def setCogMerits(self, merits):
        if not merits:
            self.notify.warning('cogMerits set to bad value: %s. Resetting to [0,0,0,0]' % merits)
            self.cogMerits = [0,
                              0,
                              0,
                              0]
        else:
            self.cogMerits = merits

    def d_setCogMerits(self, merits):
        self.sendUpdate('setCogMerits', [merits])

    def getCogMerits(self):
        return self.cogMerits

    def b_promote(self, dept):
        oldMerits = CogDisguiseGlobals.getTotalMerits(self, dept)
        self.incCogLevel(dept)

        if self.cogLevels[dept] < ToontownGlobals.MaxCogSuitLevel:
            merits = self.getCogMerits()

            if not self.hasEPP(dept):
                merits[dept] = 0

            else:
                if oldMerits >= CogDisguiseGlobals.getTotalMerits(self, dept):
                    merits[dept] = 0

                else:
                    merits[dept] = oldMerits

            self.d_setCogMerits(merits)

    def readyForPromotion(self, dept):
        merits = self.cogMerits[dept]
        totalMerits = CogDisguiseGlobals.getTotalMerits(self, dept)
        if merits >= totalMerits:
            return 1
        else:
            return 0

    def b_setCogIndex(self, index):
        self.setCogIndex(index)
        if simbase.config.GetBool('cogsuit-hack-prevent', False):
            self.d_setCogIndex(self.cogIndex)
        else:
            self.d_setCogIndex(index)

    def setCogIndex(self, index):
        if index != -1 and not ZoneUtil.canWearSuit(self.zoneId):
            if not simbase.air.cogSuitMessageSent:
                self.notify.warning('%s setCogIndex invalid: %s' % (self.doId, index))
                if simbase.config.GetBool('want-ban-wrong-suit-place', False):
                    commentStr = 'Toon %s trying to set cog index to %s in Zone: %s' % (self.doId, index, self.zoneId)
                    #simbase.air.banManager.ban(self.doId, self.DISLid, commentStr)
        else:
            self.cogIndex = index

    def d_setCogIndex(self, index):
        self.sendUpdate('setCogIndex', [index])

    def getCogIndex(self):
        return self.cogIndex

    def b_setDisguisePageFlag(self, flag):
        self.setDisguisePageFlag(flag)
        self.d_setDisguisePageFlag(flag)

    def setDisguisePageFlag(self, flag):
        self.disguisePageFlag = flag

    def d_setDisguisePageFlag(self, flag):
        self.sendUpdate('setDisguisePageFlag', [flag])

    def getDisguisePageFlag(self):
        return self.disguisePageFlag

    def b_setSosPageFlag(self, flag):
        self.setSosPageFlag(flag)
        self.d_setSosPageFlag(flag)

    def setSosPageFlag(self, flag):
        self.sosPageFlag = flag

    def d_setSosPageFlag(self, flag):
        self.sendUpdate('setSosPageFlag', [flag])

    def getSosPageFlag(self):
        return self.sosPageFlag

    def b_setFishCollection(self, genusList, speciesList, weightList):
        self.setFishCollection(genusList, speciesList, weightList)
        self.d_setFishCollection(genusList, speciesList, weightList)

    def d_setFishCollection(self, genusList, speciesList, weightList):
        self.sendUpdate('setFishCollection', [genusList, speciesList, weightList])

    def setFishCollection(self, genusList, speciesList, weightList):
        self.fishCollection = FishCollection.FishCollection()
        self.fishCollection.makeFromNetLists(genusList, speciesList, weightList)

    def getFishCollection(self):
        return self.fishCollection.getNetLists()

    def b_setMaxFishTank(self, maxTank):
        self.d_setMaxFishTank(maxTank)
        self.setMaxFishTank(maxTank)

    def d_setMaxFishTank(self, maxTank):
        self.sendUpdate('setMaxFishTank', [maxTank])

    def setMaxFishTank(self, maxTank):
        self.maxFishTank = maxTank

    def getMaxFishTank(self):
        return self.maxFishTank

    def b_setFishTank(self, genusList, speciesList, weightList):
        self.setFishTank(genusList, speciesList, weightList)
        self.d_setFishTank(genusList, speciesList, weightList)

    def d_setFishTank(self, genusList, speciesList, weightList):
        self.sendUpdate('setFishTank', [genusList, speciesList, weightList])

    def setFishTank(self, genusList, speciesList, weightList):
        self.fishTank = FishTank.FishTank()
        self.fishTank.makeFromNetLists(genusList, speciesList, weightList)

    def getFishTank(self):
        return self.fishTank.getNetLists()

    def makeRandomFishTank(self):
        self.fishTank.generateRandomTank()
        self.d_setFishTank(*self.fishTank.getNetLists())

    def addFishToTank(self, fish):
        numFish = len(self.fishTank)
        if numFish >= self.maxFishTank:
            self.notify.warning('addFishToTank: cannot add fish, tank is full')
            return 0
        elif self.fishTank.addFish(fish):
            self.d_setFishTank(*self.fishTank.getNetLists())
            return 1
        else:
            self.notify.warning('addFishToTank: addFish failed')
            return 0

    def removeFishFromTankAtIndex(self, index):
        if self.fishTank.removeFishAtIndex(index):
            self.d_setFishTank(*self.fishTank.getNetLists())
            return 1
        else:
            self.notify.warning('removeFishFromTank: cannot find fish')
            return 0

    def b_setFishingRod(self, rodId):
        self.d_setFishingRod(rodId)
        self.setFishingRod(rodId)

    def d_setFishingRod(self, rodId):
        self.sendUpdate('setFishingRod', [rodId])

    def setFishingRod(self, rodId):
        self.fishingRod = rodId

    def getFishingRod(self):
        return self.fishingRod

    def b_setFishingTrophies(self, trophyList):
        self.setFishingTrophies(trophyList)
        self.d_setFishingTrophies(trophyList)

    def setFishingTrophies(self, trophyList):
        self.notify.debug('setting fishingTrophies to %s' % trophyList)
        self.fishingTrophies = trophyList

    def d_setFishingTrophies(self, trophyList):
        self.sendUpdate('setFishingTrophies', [trophyList])

    def getFishingTrophies(self):
        return self.fishingTrophies

    def b_setQuests(self, questList):
        flattenedQuests = []
        for quest in questList:
            flattenedQuests.extend(quest)

        self.setQuests(flattenedQuests)
        self.d_setQuests(flattenedQuests)

    def d_setQuests(self, flattenedQuests):
        self.sendUpdate('setQuests', [flattenedQuests])

    def setQuests(self, flattenedQuests):
        self.notify.debug('setting quests to %s' % flattenedQuests)
        questList = []
        questLen = 5
        for i in xrange(0, len(flattenedQuests), questLen):
            questList.append(flattenedQuests[i:i + questLen])

        self.quests = questList

    def getQuests(self):
        flattenedQuests = []
        for quest in self.quests:
            flattenedQuests.extend(quest)

        return flattenedQuests

    def getQuest(self, questId, visitNpcId = None, rewardId = None):
        for quest in self.quests:
            if quest[0] != questId:
                continue
            if visitNpcId != None:
                if visitNpcId != quest[1] and visitNpcId != quest[2]:
                    continue
            if rewardId != None:
                if rewardId != quest[3]:
                    continue
            return quest

        return

    def hasQuest(self, questId, visitNpcId = None, rewardId = None):
        if self.getQuest(questId, visitNpcId=visitNpcId, rewardId=rewardId) == None:
            return False
        else:
            return True
        return

    def removeQuest(self, id, visitNpcId = None):
        index = -1
        for i in xrange(len(self.quests)):
            if self.quests[i][0] == id:
                if visitNpcId:
                    otherId = self.quests[i][2]
                    if visitNpcId == otherId:
                        index = i
                        break
                else:
                    index = i
                    break

        if index >= 0:
            del self.quests[i]
            self.b_setQuests(self.quests)
            return 1
        else:
            return 0

    def b_setHealthDisplay(self, mode):
        self.setHealthDisplay(mode)
        self.d_setHealthDisplay(mode)

    def d_setHealthDisplay(self, mode):
        self.sendUpdate('setHealthDisplay', [mode])

    def setHealthDisplay(self, mode):
        self.mode = mode

    def addQuest(self, quest, finalReward, recordHistory = 1):
        self.quests.append(quest)
        self.b_setQuests(self.quests)
        if recordHistory:
            if quest[0] != Quests.VISIT_QUEST_ID:
                newQuestHistory = self.questHistory + [quest[0]]
                while newQuestHistory.count(Quests.VISIT_QUEST_ID) != 0:
                    newQuestHistory.remove(Quests.VISIT_QUEST_ID)

                self.b_setQuestHistory(newQuestHistory)
                if finalReward:
                    newRewardHistory = self.rewardHistory + [finalReward]
                    self.b_setRewardHistory(self.rewardTier, newRewardHistory)

    def removeAllTracesOfQuest(self, questId, rewardId):
        self.notify.debug('removeAllTracesOfQuest: questId: %s rewardId: %s' % (questId, rewardId))
        self.notify.debug('removeAllTracesOfQuest: quests before: %s' % self.quests)
        removedQuest = self.removeQuest(questId)
        self.notify.debug('removeAllTracesOfQuest: quests after: %s' % self.quests)
        self.notify.debug('removeAllTracesOfQuest: questHistory before: %s' % self.questHistory)
        removedQuestHistory = self.removeQuestFromHistory(questId)
        self.notify.debug('removeAllTracesOfQuest: questHistory after: %s' % self.questHistory)
        self.notify.debug('removeAllTracesOfQuest: reward history before: %s' % self.rewardHistory)
        removedRewardHistory = self.removeRewardFromHistory(rewardId)
        self.notify.debug('removeAllTracesOfQuest: reward history after: %s' % self.rewardHistory)
        return (removedQuest, removedQuestHistory, removedRewardHistory)

    def requestDeleteQuest(self, questDesc):
        if len(questDesc) != 5:
            self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to delete invalid questDesc %s' % str(questDesc))
            self.notify.warning('%s.requestDeleteQuest(%s) -- questDesc has incorrect params' % (self, str(questDesc)))
            return
        questId = questDesc[0]
        rewardId = questDesc[3]
        if not self.hasQuest(questId, rewardId=rewardId):
            self.air.writeServerEvent('suspicious', self.doId, "Toon tried to delete quest they don't have %s" % str(questDesc))
            self.notify.warning("%s.requestDeleteQuest(%s) -- Toon doesn't have that quest" % (self, str(questDesc)))
            return
        if not Quests.isQuestJustForFun(questId, rewardId):
            self.air.writeServerEvent('suspicious', self.doId, 'Toon tried to delete non-Just For Fun quest %s' % str(questDesc))
            self.notify.warning('%s.requestDeleteQuest(%s) -- Tried to cancel non-Just For Fun quest' % (self, str(questDesc)))
            return
        removedStatus = self.removeAllTracesOfQuest(questId, rewardId)
        if 0 in removedStatus:
            self.notify.warning('%s.requestDeleteQuest(%s) -- Failed to remove quest, status=%s' % (self, str(questDesc), removedStatus))

    def b_setQuestCarryLimit(self, limit):
        self.setQuestCarryLimit(limit)
        self.d_setQuestCarryLimit(limit)

    def d_setQuestCarryLimit(self, limit):
        self.sendUpdate('setQuestCarryLimit', [limit])

    def setQuestCarryLimit(self, limit):
        self.notify.debug('setting questCarryLimit to %s' % limit)
        self.questCarryLimit = limit

    def getQuestCarryLimit(self):
        return self.questCarryLimit

    def b_setMaxCarry(self, maxCarry):
        self.setMaxCarry(maxCarry)
        self.d_setMaxCarry(maxCarry)

    def d_setMaxCarry(self, maxCarry):
        self.sendUpdate('setMaxCarry', [maxCarry])

    def setMaxCarry(self, maxCarry):
        self.maxCarry = maxCarry

    def getMaxCarry(self):
        return self.maxCarry

    def b_setCheesyEffect(self, effect, hoodId, expireTime):
        self.setCheesyEffect(effect, hoodId, expireTime)
        self.d_setCheesyEffect(effect, hoodId, expireTime)

    def d_setCheesyEffect(self, effect, hoodId, expireTime):
        self.sendUpdate('setCheesyEffect', [effect, hoodId, expireTime])

    def setCheesyEffect(self, effect, hoodId, expireTime):
        if (not simbase.air.newsManager.isHolidayRunning(ToontownGlobals.CHRISTMAS)) and effect == ToontownGlobals.CESnowMan:
            self.b_setCheesyEffect(ToontownGlobals.CENormal, hoodId, expireTime)
            self.b_setScavengerHunt([])
            return
        elif (not simbase.air.newsManager.isHolidayRunning(ToontownGlobals.HALLOWEEN)) and effect == ToontownGlobals.CEPumpkin:
            self.b_setCheesyEffect(ToontownGlobals.CENormal, hoodId, expireTime)
            self.b_setScavengerHunt([])
            return

        self.savedCheesyEffect = effect
        self.savedCheesyHoodId = hoodId
        self.savedCheesyExpireTime = expireTime
        taskName = self.uniqueName('cheesy-expires')
        taskMgr.remove(taskName)
        if expireTime and (effect != ToontownGlobals.CENormal):
            duration = expireTime * 60 - time.time()
            if duration > 0:
                taskMgr.doMethodLater(duration, self.__undoCheesyEffect, taskName)
            else:
                self.__undoCheesyEffect(None)

    def getCheesyEffect(self):
        return (self.savedCheesyEffect, self.savedCheesyHoodId, self.savedCheesyExpireTime)

    def __undoCheesyEffect(self, task):
        self.b_setCheesyEffect(ToontownGlobals.CENormal, 0, 0)
        return Task.cont

    def b_setTrackAccess(self, trackArray):
        self.setTrackAccess(trackArray)
        self.d_setTrackAccess(trackArray)

    def d_setTrackAccess(self, trackArray):
        self.sendUpdate('setTrackAccess', [trackArray])

    def setTrackAccess(self, trackArray):
        self.trackArray = trackArray

    def getTrackAccess(self):
        return self.trackArray

    def addTrackAccess(self, track):
        self.trackArray[track] = 1
        self.b_setTrackAccess(self.trackArray)

    def removeTrackAccess(self, track):
        self.trackArray[track] = 0
        self.b_setTrackAccess(self.trackArray)

    def hasTrackAccess(self, track):
        if self.trackArray and track < len(self.trackArray):
            return self.trackArray[track]
        else:
            return 0

    def fixTrackAccess(self):
        fixed = 0
        healExp, trapExp, lureExp, soundExp, throwExp, squirtExp, dropExp = self.experience.experience
        numTracks = reduce(lambda a, b: a + b, self.trackArray)
        if self.rewardTier in [0,
         1,
         2,
         3]:
            if numTracks != 2:
                self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
                self.b_setTrackAccess([0, 0, 0, 0, 1, 1, 0])
                fixed = 1
        elif self.rewardTier in [4, 5, 6]:
            if numTracks != 3:
                self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
                if self.trackArray[ToontownBattleGlobals.SOUND_TRACK] and not self.trackArray[ToontownBattleGlobals.HEAL_TRACK]:
                    self.b_setTrackAccess([0, 0, 0, 1, 1, 1, 0])
                elif self.trackArray[ToontownBattleGlobals.HEAL_TRACK] and not self.trackArray[ToontownBattleGlobals.SOUND_TRACK]:
                    self.b_setTrackAccess([1, 0, 0, 0, 1, 1, 0])
                elif soundExp >= healExp:
                    self.b_setTrackAccess([0, 0, 0, 1, 1, 1, 0])
                else:
                    self.b_setTrackAccess([1, 0, 0, 0, 1, 1, 0])
                fixed = 1
        elif self.rewardTier in [7, 8, 9, 10]:
            if numTracks != 4:
                self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
                if self.trackArray[ToontownBattleGlobals.SOUND_TRACK] and not self.trackArray[ToontownBattleGlobals.HEAL_TRACK]:
                    if dropExp >= lureExp:
                        self.b_setTrackAccess([0, 0, 0, 1, 1, 1, 1])
                    else:
                        self.b_setTrackAccess([0, 0, 1, 1, 1, 1, 0])
                elif self.trackArray[ToontownBattleGlobals.HEAL_TRACK] and not self.trackArray[ToontownBattleGlobals.SOUND_TRACK]:
                    if dropExp >= lureExp:
                        self.b_setTrackAccess([1, 0, 0, 0, 1, 1, 1])
                    else:
                        self.b_setTrackAccess([1, 0, 1, 0, 1, 1, 0])
                elif soundExp >= healExp:
                    if dropExp >= lureExp:
                        self.b_setTrackAccess([0, 0, 0, 1, 1, 1, 1])
                    else:
                        self.b_setTrackAccess([0, 0, 1, 1, 1, 1, 0])
                elif dropExp >= lureExp:
                    self.b_setTrackAccess([1, 0, 0, 0, 1, 1, 1])
                else:
                    self.b_setTrackAccess([1, 0, 1, 0, 1, 1, 0])
                fixed = 1
        elif self.rewardTier in [11, 12, 13]:
            if numTracks != 5:
                self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
                if self.trackArray[ToontownBattleGlobals.SOUND_TRACK] and not self.trackArray[ToontownBattleGlobals.HEAL_TRACK]:
                    if self.trackArray[ToontownBattleGlobals.DROP_TRACK] and not self.trackArray[ToontownBattleGlobals.LURE_TRACK]:
                        if healExp >= trapExp:
                            self.b_setTrackAccess([1, 0, 0, 1, 1, 1, 1])
                        else:
                            self.b_setTrackAccess([0, 1, 0, 1, 1, 1, 1])
                    elif healExp >= trapExp:
                        self.b_setTrackAccess([1, 0, 1, 1, 1, 1, 0])
                    else:
                        self.b_setTrackAccess([0, 1, 1, 1, 1, 1, 0])
                elif self.trackArray[ToontownBattleGlobals.HEAL_TRACK] and not self.trackArray[ToontownBattleGlobals.SOUND_TRACK]:
                    if self.trackArray[ToontownBattleGlobals.DROP_TRACK] and not self.trackArray[ToontownBattleGlobals.LURE_TRACK]:
                        if soundExp >= trapExp:
                            self.b_setTrackAccess([1, 0, 0, 1, 1, 1, 1])
                        else:
                            self.b_setTrackAccess([1, 1, 0, 0, 1, 1, 1])
                    elif soundExp >= trapExp:
                        self.b_setTrackAccess([1, 0, 1, 1, 1, 1, 0])
                    else:
                        self.b_setTrackAccess([1, 1, 1, 0, 1, 1, 0])
                fixed = 1
        elif numTracks != 6:
            self.notify.warning('bad num tracks in tier: %s, %s' % (self.rewardTier, self.trackArray))
            sortedExp = [healExp,
                         trapExp,
                         lureExp,
                         soundExp,
                         dropExp]
            sortedExp.sort()
            if trapExp == sortedExp[0]:
                self.b_setTrackAccess([1, 0, 1, 1, 1, 1, 1])
            elif lureExp == sortedExp[0]:
                self.b_setTrackAccess([1, 1, 0, 1, 1, 1, 1])
            elif dropExp == sortedExp[0]:
                self.b_setTrackAccess([1, 1, 1, 1, 1, 1, 0])
            elif soundExp == sortedExp[0]:
                self.b_setTrackAccess([1, 1, 1, 0, 1, 1, 1])
            elif healExp == sortedExp[0]:
                self.b_setTrackAccess([0, 1, 1, 1, 1, 1, 1])
            else:
                self.notify.warning('invalid exp?!: %s, %s' % (sortedExp, self.trackArray))
                self.b_setTrackAccess([1, 0, 1, 1, 1, 1, 1])
            fixed = 1
        if fixed:
            self.inventory.zeroInv()
            self.inventory.maxOutInv()
            self.d_setInventory(self.inventory.makeNetString())
            self.notify.info('fixed tracks: %s' % self.trackArray)
        return fixed

    def b_setTrackProgress(self, trackId, progress):
        self.setTrackProgress(trackId, progress)
        self.d_setTrackProgress(trackId, progress)

    def d_setTrackProgress(self, trackId, progress):
        self.sendUpdate('setTrackProgress', [trackId, progress])

    def setTrackProgress(self, trackId, progress):
        self.trackProgressId = trackId
        self.trackProgress = progress

    def addTrackProgress(self, trackId, progressIndex):
        if self.trackProgressId != trackId:
            self.notify.warning('tried to update progress on a track toon is not training')
        newProgress = self.trackProgress | 1 << progressIndex - 1
        self.b_setTrackProgress(self.trackProgressId, newProgress)

    def clearTrackProgress(self):
        self.b_setTrackProgress(-1, 0)

    def getTrackProgress(self):
        return [self.trackProgressId, self.trackProgress]

    def b_setHoodsVisited(self, hoodsVisitedArray):
        self.hoodsVisited = hoodsVisitedArray
        self.d_setHoodsVisited(hoodsVisitedArray)

    def d_setHoodsVisited(self, hoodsVisitedArray):
        self.sendUpdate('setHoodsVisited', [hoodsVisitedArray])

    def b_setTeleportAccess(self, teleportZoneArray):
        self.setTeleportAccess(teleportZoneArray)
        self.d_setTeleportAccess(teleportZoneArray)

    def d_setTeleportAccess(self, teleportZoneArray):
        self.sendUpdate('setTeleportAccess', [teleportZoneArray])

    def setTeleportAccess(self, teleportZoneArray):
        self.teleportZoneArray = teleportZoneArray

    def getTeleportAccess(self):
        return self.teleportZoneArray

    def hasTeleportAccess(self, zoneId):
        return zoneId in self.teleportZoneArray

    def addTeleportAccess(self, zoneId):
        if zoneId not in self.teleportZoneArray:
            self.teleportZoneArray.append(zoneId)
            self.b_setTeleportAccess(self.teleportZoneArray)

    def removeTeleportAccess(self, zoneId):
        if zoneId in self.teleportZoneArray:
            self.teleportZoneArray.remove(zoneId)
            self.b_setTeleportAccess(self.teleportZoneArray)

    def checkTeleportAccess(self, zoneId):
        if zoneId not in self.getTeleportAccess() and self.teleportOverride != 1:
            simbase.air.writeServerEvent('suspicious', self.doId, 'Toon teleporting to zone %s they do not have access to.' % zoneId)
            if simbase.config.GetBool('want-ban-teleport', False):
                commentStr = 'Toon %s teleporting to a zone %s they do not have access to' % (self.doId, zoneId)
                simbase.air.banManager.ban(self.doId, self.DISLid, commentStr)

    def setTeleportOverride(self, flag):
        self.teleportOverride = flag
        self.b_setHoodsVisited([1000,2000,3000,4000,5000,6000,7000,8000,9000,10000,11000,12000,13000])

    def b_setScavengerHunt(self, scavengerHuntArray):
        self.setScavengerHunt(scavengerHuntArray)
        self.d_setScavengerHunt(scavengerHuntArray)

    def d_setScavengerHunt(self, scavengerHuntArray):
        self.sendUpdate('setScavengerHunt', [scavengerHuntArray])

    def setScavengerHunt(self, scavengerHuntArray):
        self.scavengerHuntArray = scavengerHuntArray

    def getScavengerHunt(self):
        return self.scavengerHuntArray

    def b_setQuestHistory(self, questList):
        self.setQuestHistory(questList)
        self.d_setQuestHistory(questList)

    def d_setQuestHistory(self, questList):
        self.sendUpdate('setQuestHistory', [questList])

    def setQuestHistory(self, questList):
        self.notify.debug('setting quest history to %s' % questList)
        self.questHistory = questList

    def getQuestHistory(self):
        return self.questHistory

    def removeQuestFromHistory(self, questId):
        if questId in self.questHistory:
            self.questHistory.remove(questId)
            self.d_setQuestHistory(self.questHistory)
            return 1
        else:
            return 0

    def removeRewardFromHistory(self, rewardId):
        rewardTier, rewardHistory = self.getRewardHistory()
        if rewardId in rewardHistory:
            rewardHistory.remove(rewardId)
            self.b_setRewardHistory(rewardTier, rewardHistory)
            return 1
        else:
            return 0

    def b_setRewardHistory(self, tier, rewardList):
        self.setRewardHistory(tier, rewardList)
        self.d_setRewardHistory(tier, rewardList)

    def d_setRewardHistory(self, tier, rewardList):
        self.sendUpdate('setRewardHistory', [tier, rewardList])

    def setRewardHistory(self, tier, rewardList):
        self.air.writeServerEvent('questTier', self.getDoId(), str(tier))
        self.notify.debug('setting reward history to tier %s, %s' % (tier, rewardList))
        self.rewardTier = tier
        self.rewardHistory = rewardList

    def getRewardHistory(self):
        return (self.rewardTier, self.rewardHistory)

    def getRewardTier(self):
        return self.rewardTier

    def fixAvatar(self):
        anyChanged = 0
        qrc = QuestRewardCounter.QuestRewardCounter()
        if qrc.fixAvatar(self):
            self.notify.info("Fixed avatar %d's quest rewards." % self.doId)
            anyChanged = 1
        if self.hp > self.maxHp:
            self.notify.info('Changed avatar %d to have hp %d instead of %d, to fit with maxHp' % (self.doId, self.maxHp, self.hp))
            self.b_setHp(self.maxHp)
            anyChanged = 1
        inventoryChanged = 0
        carry = self.maxCarry
        for track in xrange(len(ToontownBattleGlobals.Tracks)):
            if not self.hasTrackAccess(track):
                for level in xrange(len(ToontownBattleGlobals.Levels[track])):
                    count = self.inventory.inventory[track][level]
                    if count != 0:
                        self.notify.info('Changed avatar %d to throw away %d items in track %d level %d; no access to track.' % (self.doId,
                         count,
                         track,
                         level))
                        self.inventory.inventory[track][level] = 0
                        inventoryChanged = 1

            else:
                curSkill = self.experience.getExp(track)
                for level in xrange(len(ToontownBattleGlobals.Levels[track])):
                    count = self.inventory.inventory[track][level]
                    if curSkill < ToontownBattleGlobals.Levels[track][level]:
                        if count != 0:
                            self.notify.info('Changed avatar %d to throw away %d items in track %d level %d; no access to level.' % (self.doId,
                             count,
                             track,
                             level))
                            self.inventory.inventory[track][level] = 0
                            inventoryChanged = 1
                    else:
                        newCount = min(count, carry)
                        newCount = min(count, self.inventory.getMax(track, level))
                        if count != newCount:
                            self.notify.info('Changed avatar %d to throw away %d items in track %d level %d; too many gags.' % (self.doId,
                             count - newCount,
                             track,
                             level))
                            self.inventory.inventory[track][level] = newCount
                            inventoryChanged = 1
                        carry -= newCount

        self.inventory.calcTotalProps()
        if inventoryChanged:
            self.d_setInventory(self.inventory.makeNetString())
            anyChanged = 1
        if len(self.quests) > self.questCarryLimit:
            self.notify.info('Changed avatar %d to throw out %d quests; too many quests.' % (self.doId, len(self.quests) - self.questCarryLimit))
            self.b_setQuests(self.quests[:self.questCarryLimit])
            self.fixAvatar()
            anyChanged = 1
        if not (self.emoteAccess[0] and self.emoteAccess[1] and self.emoteAccess[2] and self.emoteAccess[3] and self.emoteAccess[4]):
            self.emoteAccess[0] = 1
            self.emoteAccess[1] = 1
            self.emoteAccess[2] = 1
            self.emoteAccess[3] = 1
            self.emoteAccess[4] = 1
            self.b_setEmoteAccess(self.emoteAccess)
            self.notify.info('Changed avatar %d to have emoteAccess: %s' % (self.doId, self.emoteAccess))
            anyChanged = 1
        return anyChanged

    def b_setEmoteAccess(self, bits):
        if bits[19]:
            bits.remove(bits[19])
        if self.emoteAccess[19]:
            self.emoteAccess.remove(self.emoteAccess[19])
        self.setEmoteAccess(bits)
        self.d_setEmoteAccess(bits)

    def d_setEmoteAccess(self, bits):
        self.sendUpdate('setEmoteAccess', [bits])

    def setEmoteAccess(self, bits):
        if bits[19]:
            bits.remove(bits[19])
        if self.emoteAccess[19]:
            self.emoteAccess.remove(self.emoteAccess[19])
        maxBitCount = len(self.emoteAccess)
        bits = bits[:maxBitCount]
        bitCount = len(bits)
        if bitCount < maxBitCount:
            bits.extend([0] * (maxBitCount-bitCount))
            self.b_setEmoteAccess(bits)
        else:
            self.emoteAccess = bits

    def getEmoteAccess(self):
        return self.emoteAccess

    def setEmoteAccessId(self, id, bit):
        self.emoteAccess[id] = bit
        self.d_setEmoteAccess(self.emoteAccess)

    def b_setHouseId(self, id):
        self.setHouseId(id)
        self.d_setHouseId(id)

    def d_setHouseId(self, id):
        self.sendUpdate('setHouseId', [id])

    def setHouseId(self, id):
        self.houseId = id

    def getHouseId(self):
        return self.houseId

    def b_setCustomMessages(self, customMessages):
        self.d_setCustomMessages(customMessages)
        self.setCustomMessages(customMessages)

    def d_setCustomMessages(self, customMessages):
        self.sendUpdate('setCustomMessages', [customMessages])

    def setCustomMessages(self, customMessages):
        self.customMessages = customMessages

    def getCustomMessages(self):
        return self.customMessages

    def b_setResistanceMessages(self, resistanceMessages):
        self.d_setResistanceMessages(resistanceMessages)
        self.setResistanceMessages(resistanceMessages)

    def d_setResistanceMessages(self, resistanceMessages):
        self.sendUpdate('setResistanceMessages', [resistanceMessages])

    def setResistanceMessages(self, resistanceMessages):
        self.resistanceMessages = resistanceMessages

    def getResistanceMessages(self):
        return self.resistanceMessages

    def addResistanceMessage(self, textId):
        msgs = self.getResistanceMessages()
        for i in xrange(len(msgs)):
            if msgs[i][0] == textId:
                msgs[i][1] += 1
                if msgs[i][1] > 32767:
                    msgs[i][1] = 32767
                self.b_setResistanceMessages(msgs)
                return

        msgs.append([textId, 1])
        self.b_setResistanceMessages(msgs)

    def removeResistanceMessage(self, textId):
        msgs = self.getResistanceMessages()
        for i in xrange(len(msgs)):
            if msgs[i][0] == textId:
                msgs[i][1] -= 1
                if msgs[i][1] <= 0:
                    del msgs[i]
                self.b_setResistanceMessages(msgs)
                return 1

        self.notify.warning("Toon %s doesn't have resistance message %s" % (self.doId, textId))
        return 0

    def restockAllResistanceMessages(self, charges = 1):
        msgs = []
        for menuIndex in ResistanceChat.resistanceMenu:
            for itemIndex in ResistanceChat.getItems(menuIndex):
                textId = ResistanceChat.encodeId(menuIndex, itemIndex)
                msgs.append([textId, charges])

        self.b_setResistanceMessages(msgs)

    def b_setCatalogSchedule(self, currentWeek, nextTime):
        self.setCatalogSchedule(currentWeek, nextTime)
        self.d_setCatalogSchedule(currentWeek, nextTime)

    def d_setCatalogSchedule(self, currentWeek, nextTime):
        self.sendUpdate('setCatalogSchedule', [currentWeek, nextTime])

    def setCatalogSchedule(self, currentWeek, nextTime):
        self.catalogScheduleCurrentWeek = currentWeek
        self.catalogScheduleNextTime = nextTime
        taskName = self.uniqueName('next-catalog')
        taskMgr.remove(taskName)
        duration = max(10.0, nextTime * 60 - time.time())
        taskMgr.doMethodLater(duration, self.__deliverCatalog, taskName)

    def getCatalogSchedule(self):
        return (self.catalogScheduleCurrentWeek, self.catalogScheduleNextTime)

    def __deliverCatalog(self, task):
        self.air.catalogManager.deliverCatalogFor(self)
        return Task.done

    def b_setCatalog(self, monthlyCatalog, weeklyCatalog, backCatalog):
        self.setCatalog(monthlyCatalog, weeklyCatalog, backCatalog)
        self.d_setCatalog(monthlyCatalog, weeklyCatalog, backCatalog)

    def d_setCatalog(self, monthlyCatalog, weeklyCatalog, backCatalog):
        self.sendUpdate('setCatalog', [monthlyCatalog.getBlob(), weeklyCatalog.getBlob(), backCatalog.getBlob()])

    def setCatalog(self, monthlyCatalog, weeklyCatalog, backCatalog):
        self.monthlyCatalog = CatalogItemList.CatalogItemList(monthlyCatalog)
        self.weeklyCatalog = CatalogItemList.CatalogItemList(weeklyCatalog)
        self.backCatalog = CatalogItemList.CatalogItemList(backCatalog)

    def getCatalog(self):
        return (self.monthlyCatalog.getBlob(), self.weeklyCatalog.getBlob(), self.backCatalog.getBlob())

    def b_setCatalogNotify(self, catalogNotify, mailboxNotify):
        self.setCatalogNotify(catalogNotify, mailboxNotify)
        self.d_setCatalogNotify(catalogNotify, mailboxNotify)

    def d_setCatalogNotify(self, catalogNotify, mailboxNotify):
        self.sendUpdate('setCatalogNotify', [catalogNotify, mailboxNotify])

    def setCatalogNotify(self, catalogNotify, mailboxNotify):
        self.catalogNotify = catalogNotify
        self.mailboxNotify = mailboxNotify

    def getCatalogNotify(self):
        return (self.catalogNotify, self.mailboxNotify)

    def addToDeliverySchedule(self, item, minutes=0):
        if config.GetBool('want-instant-delivery', False):
            minutes = 0

        item.deliveryDate = int(time.time() / 60. + minutes + .5)
        self.onOrder.append(item)
        self.b_setDeliverySchedule(self.onOrder)

    def b_setDeliverySchedule(self, onOrder, doUpdateLater = True):
        self.setDeliverySchedule(onOrder, doUpdateLater)
        self.d_setDeliverySchedule(onOrder)

    def d_setDeliverySchedule(self, onOrder):
        self.sendUpdate('setDeliverySchedule', [onOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)])

    def d_setGiftSchedule(self, onGiftOrder):
        self.sendUpdate('setGiftSchedule', [self.onGiftOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)])

    def setDeliverySchedule(self, onOrder, doUpdateLater = True):
        self.setBothSchedules(onOrder, None)

    def getDeliverySchedule(self):
        return self.onOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)

    def b_setBothSchedules(self, onOrder, onGiftOrder, doUpdateLater = True):
        self.setBothSchedules(onOrder, onGiftOrder, doUpdateLater)
        self.d_setDeliverySchedule(onOrder)
        self.d_setGiftSchedule(onGiftOrder)

    def setBothSchedules(self, onOrder, onGiftOrder, doUpdateLater = True):
        if onOrder != None:
            self.onOrder = CatalogItemList.CatalogItemList(onOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if onGiftOrder != None:
            self.onGiftOrder = CatalogItemList.CatalogItemList(onGiftOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if not hasattr(self, 'air') or self.air == None:
            return
        if doUpdateLater and hasattr(self, 'name'):
            taskName = 'next-bothDelivery-%s' % self.doId
            now = int(time.time() / 60 + 0.5)
            nextItem = None
            nextGiftItem = None
            nextTime = None
            nextGiftTime = None
            if self.onOrder:
                nextTime = self.onOrder.getNextDeliveryDate()
                nextItem = self.onOrder.getNextDeliveryItem()
            if self.onGiftOrder:
                nextGiftTime = self.onGiftOrder.getNextDeliveryDate()
                nextGiftItem = self.onGiftOrder.getNextDeliveryItem()
            if nextItem:
                pass
            if nextGiftItem:
                pass
            if nextTime == None:
                nextTime = nextGiftTime
            if nextGiftTime == None:
                nextGiftTime = nextTime
            if nextGiftTime < nextTime:
                nextTime = nextGiftTime
            existingDuration = None
            checkTaskList = taskMgr.getTasksNamed(taskName)
            if checkTaskList:
                currentTime = globalClock.getFrameTime()
                checkTask = checkTaskList[0]
                existingDuration = checkTask.wakeTime - currentTime
            if nextTime:
                newDuration = max(10.0, nextTime * 60 - time.time())
                if existingDuration and existingDuration >= newDuration:
                    taskMgr.remove(taskName)
                    taskMgr.doMethodLater(newDuration, self.__deliverBothPurchases, taskName)
                elif existingDuration and existingDuration < newDuration:
                    pass
                else:
                    taskMgr.doMethodLater(newDuration, self.__deliverBothPurchases, taskName)
        return

    def __deliverBothPurchases(self, task):
        now = int(time.time() / 60 + 0.5)
        delivered, remaining = self.onOrder.extractDeliveryItems(now)
        deliveredGifts, remainingGifts = self.onGiftOrder.extractDeliveryItems(now)
        giftItem = CatalogItemList.CatalogItemList(deliveredGifts, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if len(giftItem) > 0:
            self.air.writeServerEvent('Getting Gift', self.doId, 'sender %s receiver %s gift %s' % (giftItem[0].giftTag, self.doId, giftItem[0].getName()))
        self.b_setMailboxContents(self.mailboxContents + delivered + deliveredGifts)
        self.b_setCatalogNotify(self.catalogNotify, ToontownGlobals.NewItems)
        self.b_setBothSchedules(remaining, remainingGifts)
        return Task.done

    def setGiftSchedule(self, onGiftOrder, doUpdateLater = True):
        self.setBothSchedules(None, onGiftOrder)

    def getGiftSchedule(self):
        return self.onGiftOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)

    def __deliverGiftPurchase(self, task):
        now = int(time.time() / 60 + 0.5)
        delivered, remaining = self.onGiftOrder.extractDeliveryItems(now)
        self.notify.info('Gift Delivery for %s: %s.' % (self.doId, delivered))
        self.b_setMailboxContents(self.mailboxContents + delivered)
        self.b_setCatalogNotify(self.catalogNotify, ToontownGlobals.NewItems)
        return Task.done

    def __deliverPurchase(self, task):
        now = int(time.time() / 60 + 0.5)
        delivered, remaining = self.onOrder.extractDeliveryItems(now)
        self.notify.info('Delivery for %s: %s.' % (self.doId, delivered))
        self.b_setMailboxContents(self.mailboxContents + delivered)
        self.b_setDeliverySchedule(remaining)
        self.b_setCatalogNotify(self.catalogNotify, ToontownGlobals.NewItems)
        return Task.done

    def b_setMailboxContents(self, mailboxContents):
        self.setMailboxContents(mailboxContents)
        self.d_setMailboxContents(mailboxContents)

    def d_setMailboxContents(self, mailboxContents):
        self.sendUpdate('setMailboxContents', [mailboxContents.getBlob(store=CatalogItem.Customization)])
        if len(mailboxContents) == 0:
            self.b_setCatalogNotify(self.catalogNotify, ToontownGlobals.NoItems)
        self.checkMailboxFullIndicator()

    def checkMailboxFullIndicator(self):
        pass

    def setMailboxContents(self, mailboxContents):
        self.notify.debug('Setting mailboxContents to %s.' % mailboxContents)
        self.mailboxContents = CatalogItemList.CatalogItemList(mailboxContents, store=CatalogItem.Customization)
        self.notify.debug('mailboxContents is %s.' % self.mailboxContents)

    def getMailboxContents(self):
        return self.mailboxContents.getBlob(store=CatalogItem.Customization)

    def b_setGhostMode(self, flag):
        self.setGhostMode(flag)
        self.d_setGhostMode(flag)

    def d_setGhostMode(self, flag):
        self.sendUpdate('setGhostMode', [flag])

    def setGhostMode(self, flag):
        self.ghostMode = flag

    def setImmortalMode(self, flag):
        self.immortalMode = flag

    def setUnlimitedGags(self, flag):
        self.unlimitedGags = flag

    def b_setSpeedChatStyleIndex(self, index):
        self.setSpeedChatStyleIndex(index)
        self.d_setSpeedChatStyleIndex(index)

    def d_setSpeedChatStyleIndex(self, index):
        self.sendUpdate('setSpeedChatStyleIndex', [index])

    def setSpeedChatStyleIndex(self, index):
        self.speedChatStyleIndex = index

    def getSpeedChatStyleIndex(self):
        return self.speedChatStyleIndex

    def b_setMaxMoney(self, maxMoney):
        self.d_setMaxMoney(maxMoney)
        self.setMaxMoney(maxMoney)

        if self.getMoney() > maxMoney:
            self.b_setBankMoney(self.bankMoney + (self.getMoney() - maxMoney))
            self.b_setMoney(maxMoney)

    def d_setMaxMoney(self, maxMoney):
        self.sendUpdate('setMaxMoney', [maxMoney])

    def setMaxMoney(self, maxMoney):
        self.maxMoney = maxMoney

    def getMaxMoney(self):
        return self.maxMoney

    def b_setMaxBankMoney(self, maxBankMoney):
        self.d_setMaxBankMoney(maxBankMoney)
        self.setMaxBankMoney(maxBankMoney)

        if self.getBankMoney() > maxBankMoney:
            self.b_setBankMoney(maxBankMoney)

    def d_setMaxBankMoney(self, maxBankMoney):
        self.sendUpdate('setMaxBankMoney', [maxBankMoney])

    def setMaxBankMoney(self, maxBankMoney):
        self.maxBankMoney = maxBankMoney

    def getMaxBankMoney(self):
        return self.maxBankMoney

    def addMoney(self, deltaMoney):
        if deltaMoney > 0:
            messenger.send('topToonsManager-event', [self.doId, TopToonsGlobals.CAT_JELLYBEAN, deltaMoney])
        money = deltaMoney + self.money
        pocketMoney = min(money, self.maxMoney)
        self.b_setMoney(pocketMoney)
        overflowMoney = money - self.maxMoney
        if overflowMoney > 0:
            bankMoney = self.bankMoney + overflowMoney
            self.b_setBankMoney(bankMoney)

    def takeMoney(self, deltaMoney, bUseBank = True):
        totalMoney = self.money
        if bUseBank:
            totalMoney += self.bankMoney
        if deltaMoney > totalMoney:
            self.notify.warning('Not enough money! AvId: %s Has:%s Charged:%s' % (self.doId, totalMoney, deltaMoney))
            return False
        if bUseBank and deltaMoney > self.money:
            self.b_setBankMoney(self.bankMoney - (deltaMoney - self.money))
            self.b_setMoney(0)
        else:
            self.b_setMoney(self.money - deltaMoney)
        return True

    def b_setMoney(self, money):
        if bboard.get('autoRich-%s' % self.doId, False):
            money = self.getMaxMoney()
        self.setMoney(money)
        self.d_setMoney(money)

    def d_setMoney(self, money):
        self.sendUpdate('setMoney', [money])

    def setMoney(self, money):
        if money < 0:
            simbase.air.writeServerEvent('suspicious', self.doId, 'toon has invalid money %s, forcing to zero' % money)
            money = 0
            commentStr = 'User %s has negative money %s' % (self.doId, money)
            dislId = self.DISLid
            if simbase.config.GetBool('want-ban-negative-money', False):
                simbase.air.banManager.ban(self.doId, dislId, commentStr)
        self.money = money

    def getMoney(self):
        return self.money

    def getTotalMoney(self):
        return self.money + self.bankMoney

    def b_setBankMoney(self, money):
        bankMoney = min(money, ToontownGlobals.MaxBankMoney)
        self.setBankMoney(bankMoney)
        self.d_setBankMoney(bankMoney)

    def d_setBankMoney(self, money):
        self.sendUpdate('setBankMoney', [money])

    def setBankMoney(self, money):
        self.bankMoney = money

    def getBankMoney(self):
        return self.bankMoney

    def b_setEmblems(self, emblems):
        self.setEmblems(emblems)
        self.d_setEmblems(emblems)

    def setEmblems(self, emblems):
        self.emblems = emblems

    def d_setEmblems(self, emblems):
        if simbase.air.wantEmblems:
            self.sendUpdate('setEmblems', [emblems])

    def getEmblems(self):
        return self.emblems

    def addEmblems(self, emblemsToAdd):
        newEmblems = self.emblems[:]
        for i in xrange(ToontownGlobals.NumEmblemTypes):
            newEmblems[i] += emblemsToAdd[i]

        self.b_setEmblems(newEmblems)

    def subtractEmblems(self, emblemsToSubtract):
        if len(emblemsToSubtract) < ToontownGlobals.NumEmblemTypes:
            return True

        newEmblems = self.emblems[:]
        for i in xrange(ToontownGlobals.NumEmblemTypes):
            if newEmblems[i] < emblemsToSubtract[i]:
                return False

            newEmblems[i] -= emblemsToSubtract[i]

        self.b_setEmblems(newEmblems)
        return True

    def isEnoughEmblemsToBuy(self, itemEmblemPrices):
        for emblemIndex, emblemPrice in enumerate(itemEmblemPrices):
            if emblemIndex >= len(self.emblems):
                return False
            if self.emblems[emblemIndex] < emblemPrice:
                return False

        return True



    def tossPie(self, x, y, z, h, p, r, sequence, power, timestamp32):
        if not self.validate(self.doId, self.numPies > 0, 'tossPie with no pies available'):
            return
        if self.numPies != ToontownGlobals.FullPies:
            self.b_setNumPies(self.numPies - 1)

    def b_setNumPies(self, numPies):
        self.setNumPies(numPies)
        self.d_setNumPies(numPies)

    def d_setNumPies(self, numPies):
        self.sendUpdate('setNumPies', [numPies])

    def setNumPies(self, numPies):
        self.numPies = numPies

    def b_setPieType(self, pieType):
        self.setPieType(pieType)
        self.d_setPieType(pieType)

    def d_setPieType(self, pieType):
        self.sendUpdate('setPieType', [pieType])

    def setPieType(self, pieType):
        self.pieType = pieType

    def d_setTrophyScore(self, score):
        self.sendUpdate('setTrophyScore', [score])

    def stopToonUp(self):
        taskMgr.remove(self.uniqueName('safeZoneToonUp'))
        self.ignore(self.air.getAvatarExitEvent(self.getDoId()))

    def startToonUp(self, healFrequency):
        self.stopToonUp()
        self.nextToonup = (healFrequency, self.indexOf(ToontownGlobals.TOONUP_PULSE_ZONES, ZoneUtil.getCanonicalHoodId(self.zoneId), 0) + 1)
        self.__waitForNextToonUp()

    @staticmethod
    def indexOf(list, element, default):
        try:
            return list.index(element)
        except:
            return default

    def __waitForNextToonUp(self):
        taskMgr.doMethodLater(self.nextToonup[0], self.toonUpTask, self.uniqueName('safeZoneToonUp'))

    def toonUpTask(self, task):
        self.toonUp(self.nextToonup[1])
        self.__waitForNextToonUp()
        return Task.done

    def toonUp(self, hpGained, quietly = 0, sendTotal = 1):
        if hpGained > self.maxHp:
            hpGained = self.maxHp
        if not quietly:
            self.sendUpdate('toonUp', [hpGained])
        if self.hp + hpGained <= 0:
            self.hp += hpGained
        else:
            self.hp = max(self.hp, 0) + hpGained
        clampedHp = min(self.hp, self.maxHp)
        if not self.hpOwnedByBattle:
            self.hp = clampedHp
        if sendTotal and not self.hpOwnedByBattle:
            self.d_setHp(clampedHp)

    def isToonedUp(self):
        return self.hp >= self.maxHp

    def b_announceBingo(self):
        self.d_announceBingo()
        self.announceBingo()

    def d_announceBingo(self):
        self.sendUpdate('announceBingo', [])

    def announceBingo(self):
        pass

    def incrementPopulation(self):
        if self.isPlayerControlled():
            DistributedPlayerAI.DistributedPlayerAI.incrementPopulation(self)

    def decrementPopulation(self):
        if self.isPlayerControlled():
            DistributedPlayerAI.DistributedPlayerAI.decrementPopulation()

    def reqSCResistance(self, msgIndex, nearbyPlayers):
        self.d_setSCResistance(msgIndex, nearbyPlayers)

    def d_setSCResistance(self, msgIndex, nearbyPlayers):
        if not ResistanceChat.validateId(msgIndex):
            self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s, which is invalid.' % msgIndex)
            return
        if not self.removeResistanceMessage(msgIndex):
            self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s, but does not have it.' % msgIndex)
            return
        if hasattr(self, 'autoResistanceRestock') and self.autoResistanceRestock:
            self.restockAllResistanceMessages(1)
        affectedPlayers = []
        for toonId in nearbyPlayers:
            toon = self.air.doId2do.get(toonId)
            if not toon:
                self.notify.warning('%s said resistance %s for %s; not on server' % (self.doId, msgIndex, toonId))
            elif toon.__class__ != DistributedToonAI:
                self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s for %s; object of type %s' % (msgIndex, toonId, toon.__class__.__name__))
            elif toonId in affectedPlayers:
                self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s for %s twice in same message.' % (msgIndex, toonId))
            else:
                toon.doResistanceEffect(msgIndex)
                affectedPlayers.append(toonId)

        if len(affectedPlayers) > 50:
            self.air.writeServerEvent('suspicious', self.doId, 'said resistance %s for %s toons.' % (msgIndex, len(affectedPlayers)))
            self.notify.warning('%s said resistance %s for %s toons: %s' % (self.doId,
             msgIndex,
             len(affectedPlayers),
             affectedPlayers))
        self.sendUpdate('setSCResistance', [msgIndex, affectedPlayers])
        type = ResistanceChat.getMenuName(msgIndex)
        value = ResistanceChat.getItemValue(msgIndex)
        self.air.writeServerEvent('resistanceChat', self.zoneId, '%s|%s|%s|%s' % (self.doId,
         type,
         value,
         affectedPlayers))

    def doResistanceEffect(self, msgIndex):
        msgType, itemIndex = ResistanceChat.decodeId(msgIndex)
        msgValue = ResistanceChat.getItemValue(msgIndex)
        if msgType == ResistanceChat.RESISTANCE_TOONUP:
            if msgValue == -1:
                self.toonUp(self.maxHp)
            else:
                self.toonUp(msgValue)
        elif msgType == ResistanceChat.RESISTANCE_RESTOCK:
            self.inventory.NPCMaxOutInv(msgValue)
            self.d_setInventory(self.inventory.makeNetString())
        elif msgType == ResistanceChat.RESISTANCE_MONEY:
            self.addMoney(msgValue)
        elif msgType == ResistanceChat.RESISTANCE_MERITS:
            if msgValue == -1:
                for i in xrange(len(SuitDNA.suitDepts)):
                    self.doResistanceMerits(i)
            else:
                self.doResistanceMerits(msgValue)
        elif msgType == ResistanceChat.RESISTANCE_TICKETS:
            self.b_setTickets(self.getTickets() + msgValue)

    def doResistanceMerits(self, dept):
        if not CogDisguiseGlobals.isSuitComplete(self.cogParts, dept):
            return

        totalMerits = CogDisguiseGlobals.getTotalMerits(self, dept)
        merits = self.cogMerits[dept]

        if totalMerits == 0 or merits >= totalMerits:
            return

        self.cogMerits[dept] = min(totalMerits, merits + (totalMerits / 3))
        self.b_setCogMerits(self.cogMerits)

    def squish(self, damage):
        self.takeDamage(damage)

    if simbase.wantKarts:

        def hasKart(self):
            return self.kartDNA[KartDNA.bodyType] != -1

        def b_setTickets(self, numTickets):
            if numTickets > RaceGlobals.MaxTickets:
                numTickets = RaceGlobals.MaxTickets
            self.d_setTickets(numTickets)
            self.setTickets(numTickets)

        def d_setTickets(self, numTickets):
            if numTickets > RaceGlobals.MaxTickets:
                numTickets = RaceGlobals.MaxTickets
            self.sendUpdate('setTickets', [numTickets])

        def setTickets(self, numTickets):
            if numTickets > RaceGlobals.MaxTickets:
                numTickets = RaceGlobals.MaxTickets
            self.tickets = numTickets

        def getTickets(self):
            return self.tickets

        def b_setKartingTrophies(self, trophyList):
            self.setKartingTrophies(trophyList)
            self.d_setKartingTrophies(trophyList)

        def setKartingTrophies(self, trophyList):
            self.notify.debug('setting kartingTrophies to %s' % trophyList)
            self.kartingTrophies = trophyList

        def d_setKartingTrophies(self, trophyList):
            self.sendUpdate('setKartingTrophies', [trophyList])

        def getKartingTrophies(self):
            return self.kartingTrophies

        def b_setKartingHistory(self, history):
            self.setKartingHistory(history)
            self.d_setKartingHistory(history)

        def setKartingHistory(self, history):
            self.notify.debug('setting kartingHistory to %s' % history)
            self.kartingHistory = history

        def d_setKartingHistory(self, history):
            self.sendUpdate('setKartingHistory', [history])

        def getKartingHistory(self):
            return self.kartingHistory

        def b_setKartingPersonalBest(self, bestTimes):
            best1 = bestTimes[0:6]
            best2 = bestTimes[6:]
            self.setKartingPersonalBest(best1)
            self.setKartingPersonalBest2(best2)
            self.d_setKartingPersonalBest(bestTimes)

        def d_setKartingPersonalBest(self, bestTimes):
            best1 = bestTimes[0:6]
            best2 = bestTimes[6:]
            self.sendUpdate('setKartingPersonalBest', [best1])
            self.sendUpdate('setKartingPersonalBest2', [best2])

        def setKartingPersonalBest(self, bestTimes):
            self.notify.debug('setting karting to %s' % bestTimes)
            self.kartingPersonalBest = bestTimes

        def setKartingPersonalBest2(self, bestTimes2):
            self.notify.debug('setting karting2 to %s' % bestTimes2)
            self.kartingPersonalBest2 = bestTimes2

        def getKartingPersonalBest(self):
            return self.kartingPersonalBest

        def getKartingPersonalBest2(self):
            return self.kartingPersonalBest2

        def getKartingPersonalBestAll(self):
            return self.kartingPersonalBest + self.kartingPersonalBest2

        def setKartDNA(self, kartDNA):
            self.b_setKartBodyType(kartDNA[KartDNA.bodyType])
            self.b_setKartBodyColor(kartDNA[KartDNA.bodyColor])
            self.b_setKartAccColor(kartDNA[KartDNA.accColor])
            self.b_setKartEngineBlockType(kartDNA[KartDNA.ebType])
            self.b_setKartSpoilerType(kartDNA[KartDNA.spType])
            self.b_setKartFrontWheelWellType(kartDNA[KartDNA.fwwType])
            self.b_setKartBackWheelWellType(kartDNA[KartDNA.bwwType])
            self.b_setKartRimType(kartDNA[KartDNA.rimsType])
            self.b_setKartDecalType(kartDNA[KartDNA.decalType])

        def b_setKartBodyType(self, bodyType):
            self.d_setKartBodyType(bodyType)
            self.setKartBodyType(bodyType)

        def d_setKartBodyType(self, bodyType):
            self.sendUpdate('setKartBodyType', [bodyType])

        def setKartBodyType(self, bodyType):
            self.kartDNA[KartDNA.bodyType] = bodyType

        def getKartBodyType(self):
            return self.kartDNA[KartDNA.bodyType]

        def b_setKartBodyColor(self, bodyColor):
            self.d_setKartBodyColor(bodyColor)
            self.setKartBodyColor(bodyColor)

        def d_setKartBodyColor(self, bodyColor):
            self.sendUpdate('setKartBodyColor', [bodyColor])

        def setKartBodyColor(self, bodyColor):
            self.kartDNA[KartDNA.bodyColor] = bodyColor

        def getKartBodyColor(self):
            return self.kartDNA[KartDNA.bodyColor]

        def b_setKartAccessoryColor(self, accColor):
            self.d_setKartAccessoryColor(accColor)
            self.setKartAccessoryColor(accColor)

        def d_setKartAccessoryColor(self, accColor):
            self.sendUpdate('setKartAccessoryColor', [accColor])

        def setKartAccessoryColor(self, accColor):
            self.kartDNA[KartDNA.accColor] = accColor

        def getKartAccessoryColor(self):
            return self.kartDNA[KartDNA.accColor]

        def b_setKartEngineBlockType(self, ebType):
            self.d_setKartEngineBlockType(ebType)
            self.setKartEngineBlockType(ebType)

        def d_setKartEngineBlockType(self, ebType):
            self.sendUpdate('setKartEngineBlockType', [ebType])

        def setKartEngineBlockType(self, ebType):
            self.kartDNA[KartDNA.ebType] = ebType

        def getKartEngineBlockType(self):
            return self.kartDNA[KartDNA.ebType]

        def b_setKartSpoilerType(self, spType):
            self.d_setKartSpoilerType(spType)
            self.setKartSpoilerType(spType)

        def d_setKartSpoilerType(self, spType):
            self.sendUpdate('setKartSpoilerType', [spType])

        def setKartSpoilerType(self, spType):
            self.kartDNA[KartDNA.spType] = spType

        def getKartSpoilerType(self):
            return self.kartDNA[KartDNA.spType]

        def b_setKartFrontWheelWellType(self, fwwType):
            self.d_setKartFrontWheelWellType(fwwType)
            self.setKartFrontWheelWellType(fwwType)

        def d_setKartFrontWheelWellType(self, fwwType):
            self.sendUpdate('setKartFrontWheelWellType', [fwwType])

        def setKartFrontWheelWellType(self, fwwType):
            self.kartDNA[KartDNA.fwwType] = fwwType

        def getKartFrontWheelWellType(self):
            return self.kartDNA[KartDNA.fwwType]

        def b_setKartBackWheelWellType(self, bwwType):
            self.d_setKartBackWheelWellType(bwwType)
            self.setKartBackWheelWellType(bwwType)

        def d_setKartBackWheelWellType(self, bwwType):
            self.sendUpdate('setKartBackWheelWellType', [bwwType])

        def setKartBackWheelWellType(self, bwwType):
            self.kartDNA[KartDNA.bwwType] = bwwType

        def getKartBackWheelWellType(self):
            return self.kartDNA[KartDNA.bwwType]

        def b_setKartRimType(self, rimsType):
            self.d_setKartRimType(rimsType)
            self.setKartRimType(rimsType)

        def d_setKartRimType(self, rimsType):
            self.sendUpdate('setKartRimType', [rimsType])

        def setKartRimType(self, rimsType):
            self.kartDNA[KartDNA.rimsType] = rimsType

        def getKartRimType(self):
            return self.kartDNA[KartDNA.rimsType]

        def b_setKartDecalType(self, decalType):
            self.d_setKartDecalType(decalType)
            self.setKartDecalType(decalType)

        def d_setKartDecalType(self, decalType):
            self.sendUpdate('setKartDecalType', [decalType])

        def setKartDecalType(self, decalType):
            self.kartDNA[KartDNA.decalType] = decalType

        def getKartDecalType(self):
            return self.kartDNA[KartDNA.decalType]

        def b_setKartAccessoriesOwned(self, accessories):
            self.d_setKartAccessoriesOwned(accessories)
            self.setKartAccessoriesOwned(accessories)

        def d_setKartAccessoriesOwned(self, accessories):
            self.sendUpdate('setKartAccessoriesOwned', [accessories])

        def setKartAccessoriesOwned(self, accessories):
            self.accessories = accessories

        def getKartAccessoriesOwned(self):
            owned = copy.deepcopy(self.accessories)
            while InvalidEntry in owned:
                owned.remove(InvalidEntry)

            return owned

        def addOwnedAccessory(self, accessoryId):
            print 'in add owned accessory'
            if accessoryId in AccessoryDict:
                if self.accessories.count(accessoryId) > 0:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to add accessory %s which is already owned!' % accessoryId)
                    return
                if self.accessories.count(InvalidEntry) > 0:
                    accList = list(self.accessories)
                    index = self.accessories.index(InvalidEntry)
                    accList[index] = accessoryId
                    self.b_setKartAccessoriesOwned(accList)
                else:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to add accessory %s when accessory inventory is full!' % accessoryId)
                    return
            else:
                self.air.writeServerEvent('suspicious', self.doId, 'attempt to add accessory %s which is not a valid accessory.' % accessoryId)
                return

        def removeOwnedAccessory(self, accessoryId):
            if accessoryId in AccessoryDict:
                if self.accessories.count(accessoryId) == 0:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to remove accessory %s which is not currently owned!' % accessoryId)
                    return
                else:
                    accList = list(self.accessories)
                    index = self.accessories.index(accessoryId)
                    accList[index] = InvalidEntry
                    self.air.writeServerEvent('deletedKartingAccessory', self.doId, '%s' % accessoryId)
                    self.b_setKartAccessoriesOwned(accList)
            else:
                self.air.writeServerEvent('suspicious', self.doId, 'attempt to remove accessory %s which is not a valid accessory.' % accessoryId)
                return

        def updateKartDNAField(self, dnaField, fieldValue):
            if not checkKartFieldValidity(dnaField):
                self.air.writeServerEvent('suspicious', self.doId, 'attempt to update to dna value  %s in the invalid field %s' % (fieldValue, dnaField))
                return
            if dnaField == KartDNA.bodyType:
                if fieldValue not in KartDict.keys() and fieldValue != InvalidEntry:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to update kart body to invalid body %s.' % fieldValue)
                    return
                self.b_setKartBodyType(fieldValue)
            else:
                accFields = [KartDNA.ebType,
                 KartDNA.spType,
                 KartDNA.fwwType,
                 KartDNA.bwwType,
                 KartDNA.rimsType,
                 KartDNA.decalType]
                colorFields = [KartDNA.bodyColor, KartDNA.accColor]
                if dnaField in accFields:
                    if fieldValue == InvalidEntry:
                        self.__updateKartDNAField(dnaField, fieldValue)
                    else:
                        if fieldValue not in self.accessories:
                            self.air.writeServerEvent('suspicious', self.doId, 'attempt to update to accessory %s which is not currently owned.' % fieldValue)
                            return
                        field = getAccessoryType(fieldValue)
                        if field == InvalidEntry:
                            self.air.writeServerEvent('suspicious', self.doId, 'attempt to update accessory %s in an illegal field %s' % (fieldValue, field))
                            return
                        elif field != dnaField:
                            self.air.writeServerEvent('suspicious', self.doId, 'attempt to update accessory %s in a field %s that does not match client specified field %s' % (fieldValue, field, dnaField))
                            return
                        self.__updateKartDNAField(dnaField, fieldValue)
                elif dnaField in colorFields:
                    if fieldValue == InvalidEntry:
                        self.__updateKartDNAField(dnaField, fieldValue)
                    else:
                        if fieldValue not in self.accessories:
                            if fieldValue != getDefaultColor():
                                self.air.writeServerEvent('suspicious', self.doId, 'attempt to update to color %s which is not owned!' % fieldValue)
                                return
                            elif fieldValue == getDefaultColor() and self.kartDNA[dnaField] != InvalidEntry:
                                self.air.writeServerEvent('suspicious', self.doId, 'attempt to update to default color %s which is not owned!' % fieldValue)
                                return
                        if getAccessoryType(fieldValue) != KartDNA.bodyColor:
                            self.air.writeServerEvent('suspicious', self.doId, 'attempt to update invalid color %s for dna field %s' % (fieldValue, dnaField))
                            return
                        self.__updateKartDNAField(dnaField, fieldValue)
                else:
                    self.air.writeServerEvent('suspicious', self.doId, 'attempt to udpate accessory %s in the invalid field %s' % (fieldValue, dnaField))
                    return

        def __updateKartDNAField(self, dnaField, fieldValue):
            if dnaField == KartDNA.bodyColor:
                self.b_setKartBodyColor(fieldValue)
            elif dnaField == KartDNA.accColor:
                self.b_setKartAccessoryColor(fieldValue)
            elif dnaField == KartDNA.ebType:
                self.b_setKartEngineBlockType(fieldValue)
            elif dnaField == KartDNA.spType:
                self.b_setKartSpoilerType(fieldValue)
            elif dnaField == KartDNA.fwwType:
                self.b_setKartFrontWheelWellType(fieldValue)
            elif dnaField == KartDNA.bwwType:
                self.b_setKartBackWheelWellType(fieldValue)
            elif dnaField == KartDNA.rimsType:
                self.b_setKartRimType(fieldValue)
            elif dnaField == KartDNA.decalType:
                self.b_setKartDecalType(fieldValue)

        def setAllowSoloRace(self, allowSoloRace):
            self.allowSoloRace = allowSoloRace

        def setAllowRaceTimeout(self, allowRaceTimeout):
            self.allowRaceTimeout = allowRaceTimeout

    if simbase.wantPets:

        def getPetId(self):
            return self.petId

        def b_setPetId(self, petId):
            self.d_setPetId(petId)
            self.setPetId(petId)

        def d_setPetId(self, petId):
            self.sendUpdate('setPetId', [petId])

        def setPetId(self, petId):
            self.petId = petId

        def getPetTrickPhrases(self):
            return self.petTrickPhrases

        def b_setPetTrickPhrases(self, tricks):
            self.setPetTrickPhrases(tricks)
            self.d_setPetTrickPhrases(tricks)

        def d_setPetTrickPhrases(self, tricks):
            self.sendUpdate('setPetTrickPhrases', [tricks])

        def setPetTrickPhrases(self, tricks):
            self.petTrickPhrases = tricks

        def deletePet(self):
            if self.petId == 0:
                self.notify.warning("this toon doesn't have a pet to delete!")
                return
            simbase.air.petMgr.deleteToonsPet(self.doId)

        def setPetMovie(self, petId, flag):
            self.notify.debug('setPetMovie: petId: %s, flag: %s' % (petId, flag))
            pet = simbase.air.doId2do.get(petId)
            if pet is not None:
                if pet.__class__.__name__ == 'DistributedPetAI':
                    pet.handleAvPetInteraction(flag, self.getDoId())
                else:
                    self.air.writeServerEvent('suspicious', self.doId, 'setPetMovie: playing pet movie %s on non-pet object %s' % (flag, petId))
            return

        def setPetTutorialDone(self, done):
            self.petTutorialDone = True

        def setFishBingoTutorialDone(self, done):
            self.fishBingoTutorialDone = True

        def setFishBingoMarkTutorialDone(self, done):
            self.fishBingoMarkTutorialDone = True

        def enterEstate(self, ownerId, zoneId):
            DistributedToonAI.notify.debug('enterEstate: %s %s %s' % (self.doId, ownerId, zoneId))
            if self.wasInEstate():
                self.cleanupEstateData()
            collSphere = CollisionSphere(0, 0, 0, self.getRadius())
            collNode = CollisionNode('toonColl-%s' % self.doId)
            collNode.addSolid(collSphere)
            collNode.setFromCollideMask(BitMask32.allOff())
            collNode.setIntoCollideMask(ToontownGlobals.WallBitmask)
            self.collNodePath = self.attachNewNode(collNode)
            taskMgr.add(self._moveSphere, self._getMoveSphereTaskName(), priority=OTPGlobals.AICollMovePriority)
            self.inEstate = 1
            self.estateOwnerId = ownerId
            self.estateZones = [zoneId]
            self.enterPetLook()

        def _getPetLookerBodyNode(self):
            return self.collNodePath

        def _getMoveSphereTaskName(self):
            return 'moveSphere-%s' % self.doId

        def _moveSphere(self, task):
            self.collNodePath.setZ(self.getRender(), 0)
            return Task.cont

        def isInEstate(self):
            return hasattr(self, 'inEstate') and self.inEstate

        def exitEstate(self, ownerId = None, zoneId = None):
            DistributedToonAI.notify.debug('exitEstate: %s %s %s' % (self.doId, ownerId, zoneId))
            DistributedToonAI.notify.debug('current zone: %s' % self.zoneId)
            self.exitPetLook()
            taskMgr.remove(self._getMoveSphereTaskName())
            self.collNodePath.removeNode()
            del self.collNodePath
            del self.estateOwnerId
            del self.inEstate
            self._wasInEstate = 1

        def wasInEstate(self):
            return hasattr(self, '_wasInEstate') and self._wasInEstate

        def cleanupEstateData(self):
            del self.estateZones
            del self._wasInEstate

        def setSC(self, msgId):
            DistributedToonAI.notify.debug('setSC: %s' % msgId)
            from toontown.pets import PetObserve
            PetObserve.send(self.zoneId, PetObserve.getSCObserve(msgId, self.doId))
            if msgId in [21006]:
                self.setHatePets(1)
            elif msgId in [21000,
                           21001,
                           21003,
                           21004,
                           21200,
                           21201,
                           21202,
                           21203,
                           21204,
                           21205,
                           21206]:
                self.setHatePets(0)

        def setSCCustom(self, msgId):
            DistributedToonAI.notify.debug('setSCCustom: %s' % msgId)
            from toontown.pets import PetObserve
            PetObserve.send(self.zoneId, PetObserve.getSCObserve(msgId, self.doId))

    def setHatePets(self, hate):
        self.hatePets = hate

    def takeOutKart(self, zoneId = None):
        if not self.kart:
            from toontown.racing import DistributedVehicleAI
            self.kart = DistributedVehicleAI.DistributedVehicleAI(self.air, self.doId)
            if zoneId:
                self.kart.generateWithRequired(zoneId)
            else:
                self.kart.generateWithRequired(self.zoneId)
            self.kart.start()

    def reqCogSummons(self, type, suitIndex):
        if type not in ('building', 'invasion', 'cogdo', 'skelinvasion', 'waiterinvasion', 'v2invasion'):
            self.air.writeServerEvent('suspicious', self.doId, 'invalid cog summons type: %s' % type)
            self.sendUpdate('cogSummonsResponse', ['fail', suitIndex, 0])
            return
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.air.writeServerEvent('suspicious', self.doId, 'invalid suitIndex: %s' % suitIndex)
            self.sendUpdate('cogSummonsResponse', ['fail', suitIndex, 0])
            return
        if not self.hasCogSummons(suitIndex, type):
            self.air.writeServerEvent('suspicious', self.doId, 'bogus cog summons')
            self.sendUpdate('cogSummonsResponse', ['fail', suitIndex, 0])
            return
        returnCode = None
        if type == 'building':
            returnCode = self.doBuildingTakeover(suitIndex)
        elif type == 'cogdo':
            returnCode = self.doCogdoTakeOver(suitIndex)
        elif type.endswith('invasion'):
            suitDeptIndex = suitIndex / SuitDNA.suitsPerDept
            suitTypeIndex = suitIndex % SuitDNA.suitsPerDept
            if type.startswith('v2'):
                flags = SuitInvasionGlobals.IFV2
            elif type.startswith('skel'):
                flags = SuitInvasionGlobals.IFSkelecog
            elif type.startswith('waiter'):
                flags = SuitInvasionGlobals.IFWaiter
            else:
                flags = 0
            returnCode = self.doCogInvasion(suitDeptIndex, suitTypeIndex, flags)
        if returnCode:
            if returnCode[0] == 'success':
                self.air.writeServerEvent('cogSummoned', self.doId, '%s|%s|%s' % (type, suitIndex, self.zoneId))
                self.removeCogSummonsEarned(suitIndex, type)
            self.sendUpdate('cogSummonsResponse', returnCode)
        return

    def doSummonSingleCog(self, suitIndex):
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.notify.warning('Bad suit index: %s' % suitIndex)
            return ['badIndex', suitIndex, 0]
        suitName = SuitDNA.suitHeadTypes[suitIndex]
        streetId = ZoneUtil.getBranchZone(self.zoneId)
        if streetId not in self.air.suitPlanners:
            return ['badlocation', suitIndex, 0]
        sp = self.air.suitPlanners[streetId]
        map = sp.getZoneIdToPointMap()
        zones = [self.zoneId, self.zoneId - 1, self.zoneId + 1]
        for zoneId in zones:
            if zoneId in map:
                points = map[zoneId][:]
                suit = sp.createNewSuit([], points, suitName=suitName)
                if suit:
                    return ['success', suitIndex, 0]

        return ['badlocation', suitIndex, 0]

    def doBuildingTakeover(self, suitIndex):
        streetId = ZoneUtil.getBranchZone(self.zoneId)
        if streetId not in self.air.suitPlanners:
            self.notify.warning('Street %d is not known.' % streetId)
            return ['badlocation', suitIndex, 0]
        sp = self.air.suitPlanners[streetId]
        bm = sp.buildingMgr
        building = self.findClosestDoor()
        if building == None:
            return ['badlocation', suitIndex, 0]
        level = None
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.notify.warning('Bad suit index: %s' % suitIndex)
            return ['badIndex', suitIndex, 0]
        suitName = SuitDNA.suitHeadTypes[suitIndex]
        track = SuitDNA.getSuitDept(suitName)
        type = SuitDNA.getSuitType(suitName)
        level, type, track = sp.pickLevelTypeAndTrack(None, type, track)
        building.suitTakeOver(track, level, None)
        self.notify.warning('cogTakeOver %s %s %d %d' % (track,
         level,
         building.block,
         self.zoneId))
        return ['success', suitIndex, building.doId]

    def doToonBuildingTakeover(self):
        streetId = ZoneUtil.getBranchZone(self.zoneId)
        if streetId not in self.air.suitPlanners:
            self.notify.warning('Street %d is not known.' % streetId)
            return ['badlocation', 'notknownstreet', 0]
        sp = self.air.suitPlanners[streetId]
        bm = sp.buildingMgr
        building = self.findClosestSuitDoor()
        if building == None:
            return ['badlocation', 'nobuilding', 0]
        if building.isToonBlock():
            return ['badlocation', 'toonblock', 0]
        building.toonTakeOver()
        self.notify.warning('toonTakeOverFromStreet %s %d' % (building.block,
         self.zoneId))

        return ['success', building.doId]

    def doCogdoTakeOver(self, suitIndex):
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.notify.warning('Bad suit index: %s' % suitIndex)
            return ['badIndex', suitIndex, 0]
        suitName = SuitDNA.suitHeadTypes[suitIndex]
        track = CogdoUtil.getCogdoTrack(suitName)
        if not track:
            return ['disabled', 0, 0]
        streetId = ZoneUtil.getBranchZone(self.zoneId)
        if streetId not in self.air.suitPlanners:
            self.notify.warning('Street %d is not known.' % streetId)
            return ['badlocation', 0, 0]
        building = self.findClosestDoor()
        if building == None:
            return ['badlocation', 0, 0]
        sp = self.air.suitPlanners[streetId]
        level, type, track = sp.pickLevelTypeAndTrack(None, SuitDNA.getSuitType(suitName), track)
        building.cogdoTakeOver(level, 2, track)
        return ['success', level, building.doId]

    def doCogInvasion(self, suitDeptIndex, suitTypeIndex, flags=0):
        if self.air.suitInvasionManager.getInvading():
            return ['busy', 0, 0]

        suitName = SuitDNA.getSuitName(suitDeptIndex, suitTypeIndex)
        suitIndex = SuitDNA.suitHeadTypes.index(suitName)

        if self.air.suitInvasionManager.startInvasion(
                suitDeptIndex=suitDeptIndex, suitTypeIndex=suitTypeIndex, flags=flags):
            return ['success', suitIndex, 0]

        return ['fail', suitIndex, 0]

    def b_setCogSummonsEarned(self, cogSummonsEarned):
        self.d_setCogSummonsEarned(cogSummonsEarned)
        self.setCogSummonsEarned(cogSummonsEarned)

    def d_setCogSummonsEarned(self, cogSummonsEarned):
        self.sendUpdate('setCogSummonsEarned', [cogSummonsEarned])

    def setCogSummonsEarned(self, cogSummonsEarned):
        self.cogSummonsEarned = cogSummonsEarned

    def getCogSummonsEarned(self):
        return self.cogSummonsEarned

    def restockAllCogSummons(self):
        numSuits = len(SuitDNA.suitHeadTypes)
        fullSetForSuit = 1 | 2 | 4 | 8
        allSummons = numSuits * [fullSetForSuit]
        self.b_setCogSummonsEarned(allSummons)

    def addCogSummonsEarned(self, suitIndex, type):
        summons = self.getCogSummonsEarned()
        curSetting = summons[suitIndex]
        if type == 'building':
            curSetting |= 1
        elif type == 'invasion':
            curSetting |= 2
        elif type == 'cogdo':
            curSetting |= 4
        elif type == 'skelinvasion':
            curSetting |= 8
        elif type == 'waiterinvasion':
            curSetting |= 16
        elif type == 'v2invasion':
            curSetting |= 32
        summons[suitIndex] = curSetting
        self.b_setCogSummonsEarned(summons)

    def removeCogSummonsEarned(self, suitIndex, type):
        summons = self.getCogSummonsEarned()
        curSetting = summons[suitIndex]
        if self.hasCogSummons(suitIndex, type):
            if type == 'building':
                curSetting &= -2
            elif type == 'invasion':
                curSetting &= -3
            elif type == 'cogdo':
                curSetting &= -5
            elif type == 'skelinvasion':
                curSetting &= -9
            elif type == 'waiterinvasion':
                curSetting &= -17
            elif type == 'v2invasion':
                curSetting &= -33
            summons[suitIndex] = curSetting
            self.b_setCogSummonsEarned(summons)
            if hasattr(self, 'autoRestockSummons') and self.autoRestockSummons:
                self.restockAllCogSummons()
            return True
        self.notify.warning("Toon %s doesn't have a %s summons for %s" % (self.doId, type, suitIndex))
        return False

    def hasCogSummons(self, suitIndex, type = None):
        summons = self.getCogSummonsEarned()
        curSetting = summons[suitIndex]
        if type == 'building':
            return curSetting & 1
        elif type == 'invasion':
            return curSetting & 2
        elif type == 'cogdo':
            return curSetting & 4
        elif type == 'skelinvasion':
            return curSetting & 8
        elif type == 'waiterinvasion':
            return curSetting & 16
        elif type == 'v2invasion':
            return curSetting & 32
        return curSetting

    def hasParticularCogSummons(self, deptIndex, level, type):
        if deptIndex not in xrange(len(SuitDNA.suitDepts)):
            self.notify.warning('invalid parameter deptIndex %s' % deptIndex)
            return False
        if level not in xrange(SuitDNA.suitsPerDept):
            self.notify.warning('invalid parameter level %s' % level)
            return False
        suitIndex = deptIndex * SuitDNA.suitsPerDept + level
        retval = self.hasCogSummons(suitIndex, type)
        return retval

    def assignNewCogSummons(self, level = None, summonType = None, deptIndex = None):
        if level != None:
            if deptIndex in xrange(len(SuitDNA.suitDepts)):
                dept = deptIndex
            else:
                numDepts = len(SuitDNA.suitDepts)
                dept = random.randrange(0, numDepts)
            suitIndex = dept * SuitDNA.suitsPerDept + level
        elif deptIndex in xrange(len(SuitDNA.suitDepts)):
            randomLevel = random.randrange(0, SuitDNA.suitsPerDept)
            suitIndex = deptIndex * SuitDNA.suitsPerLevel + randomLevel
        else:
            numSuits = len(SuitDNA.suitHeadTypes)
            suitIndex = random.randrange(0, numSuits)
        summonTypes = ['building', 'invasion', 'cogdo', 'skelinvasion', 'waiterinvasion', 'v2invasion']
        if summonType in summonTypes:
            type = summonType
        else:
            #typeWeights = ['single'] * 70 + ['building'] * 25 + ['invasion'] * 5
            type = random.choice(summonTypes)
        if suitIndex >= len(SuitDNA.suitHeadTypes):
            self.notify.warning('Bad suit index: %s' % suitIndex)
        self.addCogSummonsEarned(suitIndex, type)
        return (suitIndex, type)

    def findClosestDoor(self):
        zoneId = self.zoneId
        streetId = ZoneUtil.getBranchZone(zoneId)
        sp = self.air.suitPlanners[streetId]
        if not sp:
            return None
        bm = sp.buildingMgr
        if not bm:
            return None
        zones = [zoneId,
                 zoneId - 1,
                 zoneId + 1,
                 zoneId - 2,
                 zoneId + 2]
        for zone in zones:
            for i in bm.getToonBlocks():
                building = bm.getBuilding(i)
                extZoneId, intZoneId = building.getExteriorAndInteriorZoneId()
                if not NPCToons.isZoneProtected(intZoneId):
                    if hasattr(building, 'door'):
                        if building.door.zoneId == zone:
                            return building

        return None

    def findClosestSuitDoor(self):
        zoneId = self.zoneId
        streetId = ZoneUtil.getBranchZone(zoneId)
        sp = self.air.suitPlanners[streetId]
        if not sp:
            return None
        bm = sp.buildingMgr
        if not bm:
            return None
        zones = [zoneId,
                 zoneId - 1,
                 zoneId + 1,
                 zoneId - 2,
                 zoneId + 2]
        for zone in zones:
            for i in bm.getSuitBlocks():
                building = bm.getBuilding(i)
                extZoneId, intZoneId = building.getExteriorAndInteriorZoneId()
                if not NPCToons.isZoneProtected(intZoneId):
                    if hasattr(building, 'elevator'):
                        if building.elevator.zoneId == zone:
                            return building

        return None

    def b_setGardenTrophies(self, trophyList):
        self.setGardenTrophies(trophyList)
        self.d_setGardenTrophies(trophyList)

    def setGardenTrophies(self, trophyList):
        self.notify.debug('setting gardenTrophies to %s' % trophyList)
        self.gardenTrophies = trophyList

    def d_setGardenTrophies(self, trophyList):
        self.sendUpdate('setGardenTrophies', [trophyList])

    def getGardenTrophies(self):
        return self.gardenTrophies

    def setGardenSpecials(self, specials):
        for special in specials:
            if special[1] > 255:
                special[1] = 255

        self.gardenSpecials = specials

    def getGardenSpecials(self):
        return self.gardenSpecials

    def d_setGardenSpecials(self, specials):
        self.sendUpdate('setGardenSpecials', [specials])

    def b_setGardenSpecials(self, specials):
        for special in specials:
            if special[1] > 255:
                newCount = 255
                index = special[0]
                self.gardenSpecials.remove(special)
                self.gardenSpecials.append((index, newCount))
                self.gardenSpecials.sort()

        self.setGardenSpecials(specials)
        self.d_setGardenSpecials(specials)

    def addGardenItem(self, index, count):
        for item in self.gardenSpecials:
            if item[0] == index:
                newCount = item[1] + count
                self.gardenSpecials.remove(item)
                self.gardenSpecials.append((index, newCount))
                self.gardenSpecials.sort()
                self.b_setGardenSpecials(self.gardenSpecials)
                return

        self.gardenSpecials.append((index, count))
        self.gardenSpecials.sort()
        self.b_setGardenSpecials(self.gardenSpecials)

    def removeGardenItem(self, index, count):
        for item in self.gardenSpecials:
            if item[0] == index:
                newCount = item[1] - count
                self.gardenSpecials.remove(item)
                if newCount > 0:
                    self.gardenSpecials.append((index, newCount))
                self.gardenSpecials.sort()
                self.b_setGardenSpecials(self.gardenSpecials)
                return 1

        self.notify.warning("removing garden item %d that toon doesn't have" % index)
        return 0

    def b_setFlowerCollection(self, speciesList, varietyList):
        self.setFlowerCollection(speciesList, varietyList)
        self.d_setFlowerCollection(speciesList, varietyList)

    def d_setFlowerCollection(self, speciesList, varietyList):
        self.sendUpdate('setFlowerCollection', [speciesList, varietyList])

    def setFlowerCollection(self, speciesList, varietyList):
        self.flowerCollection = FlowerCollection.FlowerCollection()
        self.flowerCollection.makeFromNetLists(speciesList, varietyList)

    def getFlowerCollection(self):
        return self.flowerCollection.getNetLists()

    def b_setMaxFlowerBasket(self, maxFlowerBasket):
        self.d_setMaxFlowerBasket(maxFlowerBasket)
        self.setMaxFlowerBasket(maxFlowerBasket)

    def d_setMaxFlowerBasket(self, maxFlowerBasket):
        self.sendUpdate('setMaxFlowerBasket', [maxFlowerBasket])

    def setMaxFlowerBasket(self, maxFlowerBasket):
        self.maxFlowerBasket = maxFlowerBasket

    def getMaxFlowerBasket(self):
        return self.maxFlowerBasket

    def b_setFlowerBasket(self, speciesList, varietyList):
        self.setFlowerBasket(speciesList, varietyList)
        self.d_setFlowerBasket(speciesList, varietyList)

    def d_setFlowerBasket(self, speciesList, varietyList):
        self.sendUpdate('setFlowerBasket', [speciesList, varietyList])

    def setFlowerBasket(self, speciesList, varietyList):
        self.flowerBasket = FlowerBasket.FlowerBasket()
        self.flowerBasket.makeFromNetLists(speciesList, varietyList)

    def getFlowerBasket(self):
        return self.flowerBasket.getNetLists()

    def makeRandomFlowerBasket(self):
        self.flowerBasket.generateRandomBasket()
        self.d_setFlowerBasket(*self.flowerBasket.getNetLists())

    def addFlowerToBasket(self, species, variety):
        numFlower = len(self.flowerBasket)
        if numFlower >= self.maxFlowerBasket:
            self.notify.warning('addFlowerToBasket: cannot add flower, basket is full')
            return 0
        elif self.flowerBasket.addFlower(species, variety):
            self.d_setFlowerBasket(*self.flowerBasket.getNetLists())
            return 1
        else:
            self.notify.warning('addFlowerToBasket: addFlower failed')
            return 0

    def removeFlowerFromBasketAtIndex(self, index):
        if self.flowerBasket.removeFlowerAtIndex(index):
            self.d_setFlowerBasket(*self.flowerBasket.getNetLists())
            return 1
        else:
            self.notify.warning('removeFishFromTank: cannot find fish')
            return 0

    def b_setShovel(self, shovelId):
        self.d_setShovel(shovelId)
        self.setShovel(shovelId)

    def d_setShovel(self, shovelId):
        self.sendUpdate('setShovel', [shovelId])

    def setShovel(self, shovelId):
        self.shovel = shovelId

    def getShovel(self):
        return self.shovel

    def b_setShovelSkill(self, skillLevel):
        self.sendGardenEvent()
        if skillLevel >= GardenGlobals.ShovelAttributes[self.shovel]['skillPts']:
            if self.shovel < GardenGlobals.MAX_SHOVELS - 1:
                self.b_setShovel(self.shovel + 1)
                self.setShovelSkill(0)
                self.d_setShovelSkill(0)
                self.sendUpdate('promoteShovel', [self.shovel])
                self.air.writeServerEvent('garden_new_shovel', self.doId, '%d' % self.shovel)
        else:
            self.setShovelSkill(skillLevel)
            self.d_setShovelSkill(skillLevel)

    def d_setShovelSkill(self, skillLevel):
        self.sendUpdate('setShovelSkill', [skillLevel])

    def setShovelSkill(self, skillLevel):
        self.shovelSkill = skillLevel

    def getShovelSkill(self):
        return self.shovelSkill

    def b_setWateringCan(self, wateringCanId):
        self.d_setWateringCan(wateringCanId)
        self.setWateringCan(wateringCanId)

    def d_setWateringCan(self, wateringCanId):
        self.sendUpdate('setWateringCan', [wateringCanId])

    def setWateringCan(self, wateringCanId):
        self.wateringCan = wateringCanId

    def getWateringCan(self):
        return self.wateringCan

    def b_setWateringCanSkill(self, skillLevel):
        self.sendGardenEvent()
        if skillLevel >= GardenGlobals.WateringCanAttributes[self.wateringCan]['skillPts']:
            if self.wateringCan < GardenGlobals.MAX_WATERING_CANS - 1:
                self.b_setWateringCan(self.wateringCan + 1)
                self.setWateringCanSkill(0)
                self.d_setWateringCanSkill(0)
                self.sendUpdate('promoteWateringCan', [self.wateringCan])
                self.air.writeServerEvent('garden_new_wateringCan', self.doId, '%d' % self.wateringCan)
            else:
                skillLevel = GardenGlobals.WateringCanAttributes[self.wateringCan]['skillPts'] - 1
                self.setWateringCanSkill(skillLevel)
                self.d_setWateringCanSkill(skillLevel)
        else:
            self.setWateringCanSkill(skillLevel)
            self.d_setWateringCanSkill(skillLevel)

    def d_setWateringCanSkill(self, skillLevel):
        self.sendUpdate('setWateringCanSkill', [skillLevel])

    def setWateringCanSkill(self, skillLevel):
        self.wateringCanSkill = skillLevel

    def getWateringCanSkill(self):
        return self.wateringCanSkill

    def b_setTrackBonusLevel(self, trackBonusLevelArray):
        self.setTrackBonusLevel(trackBonusLevelArray)
        self.d_setTrackBonusLevel(trackBonusLevelArray)

    def d_setTrackBonusLevel(self, trackBonusLevelArray):
        self.sendUpdate('setTrackBonusLevel', [trackBonusLevelArray])

    def setTrackBonusLevel(self, trackBonusLevelArray):
        self.trackBonusLevel = trackBonusLevelArray

    def getTrackBonusLevel(self, track = None):
        if track == None:
            return self.trackBonusLevel
        else:
            return self.trackBonusLevel[track]
        return

    def checkGagBonus(self, track, level):
        trackBonus = self.getTrackBonusLevel(track)
        return trackBonus >= level

    def giveMeSpecials(self, id = None):
        print 'Specials Go!!'
        self.b_setGardenSpecials([(0, 3),
                                  (1, 2),
                                  (2, 3),
                                  (3, 2),
                                  (4, 3),
                                  (5, 2),
                                  (6, 3),
                                  (7, 2),
                                  (100, 1),
                                  (101, 3),
                                  (102, 1)])

    def reqUseSpecial(self, special):
        response = self.tryToUseSpecial(special)
        self.sendUpdate('useSpecialResponse', [response])

    def tryToUseSpecial(self, special):
        estateOwnerDoId = simbase.air.estateMgr.zone2owner.get(self.zoneId)
        response = 'badlocation'
        doIHaveThisSpecial = False
        for curSpecial in self.gardenSpecials:
            if curSpecial[0] == special and curSpecial[1] > 0:
                doIHaveThisSpecial = True
                break

        if not doIHaveThisSpecial:
            return response
        if not self.doId == estateOwnerDoId:
            self.notify.warning("how did this happen, planting an item you don't own")
            return response
        if estateOwnerDoId:
            estate = simbase.air.estateMgr.estate.get(estateOwnerDoId)
            if estate and hasattr(estate, 'avIdList'):
                ownerIndex = estate.avIdList.index(estateOwnerDoId)
                if ownerIndex >= 0:
                    estate.doEpochNow(onlyForThisToonIndex=ownerIndex)
                    self.removeGardenItem(special, 1)
                    response = 'success'
                    self.air.writeServerEvent('garden_fertilizer', self.doId, '')
        return response

    def sendGardenEvent(self):
        if hasattr(self, 'estateZones') and hasattr(self, 'doId'):
            if simbase.wantPets and self.hatePets:
                PetObserve.send(self.estateZones, PetObserve.PetActionObserve(PetObserve.Actions.GARDEN, self.doId))

    def setGardenStarted(self, bStarted):
        self.gardenStarted = bStarted

    def d_setGardenStarted(self, bStarted):
        self.sendUpdate('setGardenStarted', [bStarted])

    def b_setGardenStarted(self, bStarted):
        self.setGardenStarted(bStarted)
        self.d_setGardenStarted(bStarted)

    def getGardenStarted(self):
        return self.gardenStarted

    def logSuspiciousEvent(self, eventName):
        senderId = self.air.getAvatarIdFromSender()
        eventStr = 'senderId=%s ' % senderId
        eventStr += eventName
        self.air.writeServerEvent('suspicious', self.doId, eventStr)
        if simbase.config.GetBool('want-ban-setAnimState', True):
            if eventName.startswith('setAnimState: '):
                if senderId == self.doId:
                    commentStr = 'Toon %s trying to call setAnimState' % self.doId
                    simbase.air.banManager.ban(self.doId, self.DISLid, commentStr)
                else:
                    self.notify.warning('logSuspiciousEvent event=%s senderId=%s != self.doId=%s' % (eventName, senderId, self.doId))

    def getGolfTrophies(self):
        return self.golfTrophies

    def getGolfCups(self):
        return self.golfCups

    def b_setGolfHistory(self, history):
        self.setGolfHistory(history)
        self.d_setGolfHistory(history)

    def d_setGolfHistory(self, history):
        self.sendUpdate('setGolfHistory', [history])

    def setGolfHistory(self, history):
        self.notify.debug('setting golfHistory to %s' % history)
        self.golfHistory = history
        self.golfTrophies = GolfGlobals.calcTrophyListFromHistory(self.golfHistory)
        self.golfCups = GolfGlobals.calcCupListFromHistory(self.golfHistory)

    def getGolfHistory(self):
        return self.golfHistory

    def b_setGolfHoleBest(self, holeBest):
        self.setGolfHoleBest(holeBest)
        self.d_setGolfHoleBest(holeBest)

    def d_setGolfHoleBest(self, holeBest):
        packed = GolfGlobals.packGolfHoleBest(holeBest)
        self.sendUpdate('setPackedGolfHoleBest', [packed])

    def setGolfHoleBest(self, holeBest):
        self.golfHoleBest = holeBest

    def getGolfHoleBest(self):
        return self.golfHoleBest

    def getPackedGolfHoleBest(self):
        packed = GolfGlobals.packGolfHoleBest(self.golfHoleBest)
        return packed

    def setPackedGolfHoleBest(self, packedHoleBest):
        unpacked = GolfGlobals.unpackGolfHoleBest(packedHoleBest)
        self.setGolfHoleBest(unpacked)

    def b_setGolfCourseBest(self, courseBest):
        self.setGolfCourseBest(courseBest)
        self.d_setGolfCourseBest(courseBest)

    def d_setGolfCourseBest(self, courseBest):
        self.sendUpdate('setGolfCourseBest', [courseBest])

    def setGolfCourseBest(self, courseBest):
        self.golfCourseBest = courseBest

    def getGolfCourseBest(self):
        return self.golfCourseBest

    def setUnlimitedSwing(self, unlimitedSwing):
        self.unlimitedSwing = unlimitedSwing

    def getUnlimitedSwing(self):
        return self.unlimitedSwing

    def b_setUnlimitedSwing(self, unlimitedSwing):
        self.setUnlimitedSwing(unlimitedSwing)
        self.d_setUnlimitedSwing(unlimitedSwing)

    def d_setUnlimitedSwing(self, unlimitedSwing):
        self.sendUpdate('setUnlimitedSwing', [unlimitedSwing])

    def b_setPinkSlips(self, pinkSlips):
        self.specialInventory[0] = pinkSlips
        self.b_setSpecialInventory(self.specialInventory)

    def b_setCrateKeys(self, crateKeys):
        self.specialInventory[1] = crateKeys
        self.b_setSpecialInventory(self.specialInventory)

    def b_setSpecialInventory(self, specialInventory):
        self.d_setSpecialInventory(specialInventory)
        self.setSpecialInventory(specialInventory)

    def d_setSpecialInventory(self, specialInventory):
        self.sendUpdate('setSpecialInventory', [specialInventory])

    def setSpecialInventory(self, specialInventory):
        self.specialInventory = specialInventory

    def getPinkSlips(self):
        return self.specialInventory[0]

    def getCrateKeys(self):
        return self.specialInventory[1]

    def addPinkSlips(self, amountToAdd):
        pinkSlips = min(self.getPinkSlips() + amountToAdd, 255)
        self.b_setPinkSlips(pinkSlips)

    def removePinkSlips(self, amount):
        if hasattr(self, 'autoRestockPinkSlips') and self.autoRestockPinkSlips:
            amount = 0
        pinkSlips = max(self.getPinkSlips() - amount, 0)
        self.b_setPinkSlips(pinkSlips)

    def addCrateKeys(self, amountToAdd):
        self.b_setCrateKeys(min(self.getCrateKeys() + amountToAdd, 255))

    def removeCrateKeys(self, amount):
        self.b_setCrateKeys(max(self.getCrateKeys() - amount, 0))

    def b_setNametagStyle(self, nametagStyle):
        self.d_setNametagStyle(nametagStyle)
        self.setNametagStyle(nametagStyle)

    def d_setNametagStyle(self, nametagStyle):
        self.sendUpdate('setNametagStyle', [nametagStyle])

    def setNametagStyle(self, nametagStyle):
        self.nametagStyle = nametagStyle

    def getNametagStyle(self):
        return self.nametagStyle

    def b_setNametagStyles(self, nametagStyles):
        self.d_setNametagStyles(nametagStyles)
        self.setNametagStyles(nametagStyles)

    def d_setNametagStyles(self, nametagStyles):
        self.sendUpdate('setNametagStyles', [nametagStyles])

    def setNametagStyles(self, nametagStyles):
        self.nametagStyles = nametagStyles

    def addNametagStyle(self, nametagStyle):
        if nametagStyle in self.nametagStyles:
            return

        self.nametagStyles.append(nametagStyle)
        self.b_setNametagStyles(self.nametagStyles)

    def getNametagStyles(self):
        return self.nametagStyles

    def requestNametagStyle(self, nametagStyle):
        if nametagStyle not in self.nametagStyles:
            return

        self.b_setNametagStyle(nametagStyle)

    def b_setMail(self, mail):
        self.d_setMail(mail)
        self.setMail(mail)

    def d_setMail(self, mail):
        self.sendUpdate('setMail', [mail])

    def setMail(self, mail):
        self.mail = mail

    def setNumMailItems(self, numMailItems):
        self.numMailItems = numMailItems

    def setSimpleMailNotify(self, simpleMailNotify):
        self.simpleMailNotify = simpleMailNotify

    def setInviteMailNotify(self, inviteMailNotify):
        self.inviteMailNotify = inviteMailNotify

    def setInvites(self, invites):
        self.invites = []
        for i in xrange(len(invites)):
            oneInvite = invites[i]
            newInvite = InviteInfoBase(*oneInvite)
            self.invites.append(newInvite)

    def updateInviteMailNotify(self):
        invitesInMailbox = self.getInvitesToShowInMailbox()
        newInvites = 0
        readButNotRepliedInvites = 0
        for invite in invitesInMailbox:
            if invite.status == PartyGlobals.InviteStatus.NotRead:
                newInvites += 1
            elif invite.status == PartyGlobals.InviteStatus.ReadButNotReplied:
                readButNotRepliedInvites += 1

        if newInvites:
            self.setInviteMailNotify(ToontownGlobals.NewItems)
        elif readButNotRepliedInvites:
            self.setInviteMailNotify(ToontownGlobals.OldItems)
        else:
            self.setInviteMailNotify(ToontownGlobals.NoItems)

    def getNumNonResponseInvites(self):
        count = 0
        for i in xrange(len(self.invites)):
            if self.invites[i].status == InviteStatus.NotRead or self.invites[i].status == InviteStatus.ReadButNotReplied:
                count += 1

        return count

    def getInvitesToShowInMailbox(self):
        result = []
        for invite in self.invites:
            appendInvite = True
            if invite.status == InviteStatus.Accepted or invite.status == InviteStatus.Rejected:
                appendInvite = False
            if appendInvite:
                partyInfo = self.getOnePartyInvitedTo(invite.partyId)
                if not partyInfo:
                    appendInvite = False
                if appendInvite:
                    if partyInfo.status == PartyGlobals.PartyStatus.Cancelled:
                        appendInvite = False
                if appendInvite:
                    endDate = partyInfo.endTime.date()
                    curDate = simbase.air.toontownTimeManager.getCurServerDateTime().date()
                    if endDate < curDate:
                        appendInvite = False
            if appendInvite:
                result.append(invite)

        return result

    def getNumInvitesToShowInMailbox(self):
        result = len(self.getInvitesToShowInMailbox())
        return result

    def setHostedParties(self, hostedParties):
        self.hostedParties = []
        for i in xrange(len(hostedParties)):
            hostedInfo = hostedParties[i]
            newParty = PartyInfoAI(*hostedInfo)
            self.hostedParties.append(newParty)

    def setPartiesInvitedTo(self, partiesInvitedTo):
        self.partiesInvitedTo = []
        for i in xrange(len(partiesInvitedTo)):
            partyInfo = partiesInvitedTo[i]
            newParty = PartyInfoAI(*partyInfo)
            self.partiesInvitedTo.append(newParty)

        self.updateInviteMailNotify()
        self.checkMailboxFullIndicator()

    def getOnePartyInvitedTo(self, partyId):
        result = None
        for i in xrange(len(self.partiesInvitedTo)):
            partyInfo = self.partiesInvitedTo[i]
            if partyInfo.partyId == partyId:
                result = partyInfo
                break

        return result

    def setPartyReplyInfoBases(self, replies):
        self.partyReplyInfoBases = []
        for i in xrange(len(replies)):
            partyReply = replies[i]
            repliesForOneParty = PartyReplyInfoBase(*partyReply)
            self.partyReplyInfoBases.append(repliesForOneParty)

    def updateInvite(self, inviteKey, newStatus):
        for invite in self.invites:
            if invite.inviteKey == inviteKey:
                invite.status = newStatus
                self.updateInviteMailNotify()
                self.checkMailboxFullIndicator()
                break

    def updateReply(self, partyId, inviteeId, newStatus):
        for partyReply in self.partyReplyInfoBases:
            if partyReply.partyId == partyId:
                for reply in partyReply.replies:
                    if reply.inviteeId == inviteeId:
                        reply.inviteeId = newStatus
                        break

    def canPlanParty(self):
        nonCancelledPartiesInTheFuture = 0
        for partyInfo in self.hostedParties:
            if partyInfo.status not in (PartyGlobals.PartyStatus.Cancelled, PartyGlobals.PartyStatus.Finished, PartyGlobals.PartyStatus.NeverStarted):
                nonCancelledPartiesInTheFuture += 1
                if nonCancelledPartiesInTheFuture >= PartyGlobals.MaxHostedPartiesPerToon:
                    break

        result = nonCancelledPartiesInTheFuture < PartyGlobals.MaxHostedPartiesPerToon
        return result

    def setPartyCanStart(self, partyId):
        self.notify.debug('setPartyCanStart called passing in partyId=%s' % partyId)
        found = False
        for partyInfo in self.hostedParties:
            if partyInfo.partyId == partyId:
                partyInfo.status = PartyGlobals.PartyStatus.CanStart
                found = True
                break

        if not found:
            self.notify.warning("setPartyCanStart can't find partyId %s" % partyId)

    def setPartyStatus(self, partyId, newStatus):
        self.notify.debug('setPartyStatus  called passing in partyId=%s newStauts=%d' % (partyId, newStatus))
        found = False
        for partyInfo in self.hostedParties:
            if partyInfo.partyId == partyId:
                partyInfo.status = newStatus
                found = True
                break

        info = self.getOnePartyInvitedTo(partyId)
        if info:
            found = True
            info.status = newStatus
        if not found:
            self.notify.warning("setPartyCanStart can't find hosted or invitedTO partyId %s" % partyId)

    def b_setAwardMailboxContents(self, awardMailboxContents):
        self.setAwardMailboxContents(awardMailboxContents)
        self.d_setAwardMailboxContents(awardMailboxContents)

    def d_setAwardMailboxContents(self, awardMailboxContents):
        self.sendUpdate('setAwardMailboxContents', [awardMailboxContents.getBlob(store=CatalogItem.Customization)])

    def setAwardMailboxContents(self, awardMailboxContents):
        self.notify.debug('Setting awardMailboxContents to %s.' % awardMailboxContents)
        self.awardMailboxContents = CatalogItemList.CatalogItemList(awardMailboxContents, store=CatalogItem.Customization)
        self.notify.debug('awardMailboxContents is %s.' % self.awardMailboxContents)
        if len(awardMailboxContents) == 0:
            self.b_setAwardNotify(ToontownGlobals.NoItems)
        self.checkMailboxFullIndicator()

    def getAwardMailboxContents(self):
        return self.awardMailboxContents.getBlob(store=CatalogItem.Customization)

    def b_setAwardSchedule(self, onOrder, doUpdateLater = True):
        self.setAwardSchedule(onOrder, doUpdateLater)
        self.d_setAwardSchedule(onOrder)

    def d_setAwardSchedule(self, onOrder):
        self.sendUpdate('setAwardSchedule', [onOrder.getBlob(store=CatalogItem.Customization | CatalogItem.DeliveryDate)])

    def setAwardSchedule(self, onAwardOrder, doUpdateLater = True):
        self.onAwardOrder = CatalogItemList.CatalogItemList(onAwardOrder, store=CatalogItem.Customization | CatalogItem.DeliveryDate)
        if hasattr(self, 'name'):
            if doUpdateLater and hasattr(self, 'air'):
                taskName = self.uniqueName('next-award-delivery')
                taskMgr.remove(taskName)
                now = int(time.time() / 60 + 0.5)
                nextItem = None
                nextTime = self.onAwardOrder.getNextDeliveryDate()
                nextItem = self.onAwardOrder.getNextDeliveryItem()
                if nextItem != None:
                    pass
                if nextTime != None:
                    duration = max(10.0, nextTime * 60 - time.time())
                    taskMgr.doMethodLater(duration, self.__deliverAwardPurchase, taskName)
        return

    def __deliverAwardPurchase(self, task):
        now = int(time.time() / 60 + 0.5)
        delivered, remaining = self.onAwardOrder.extractDeliveryItems(now)
        self.notify.info('Award Delivery for %s: %s.' % (self.doId, delivered))
        self.b_setAwardMailboxContents(self.awardMailboxContents + delivered)
        self.b_setAwardSchedule(remaining)
        if delivered:
            self.b_setAwardNotify(ToontownGlobals.NewItems)
        return Task.done

    def b_setAwardNotify(self, awardMailboxNotify):
        self.setAwardNotify(awardMailboxNotify)
        self.d_setAwardNotify(awardMailboxNotify)

    def d_setAwardNotify(self, awardMailboxNotify):
        self.sendUpdate('setAwardNotify', [awardMailboxNotify])

    def setAwardNotify(self, awardNotify):
        self.awardNotify = awardNotify

    def teleportResponseToAI(self, toAvId, available, shardId, hoodId, zoneId, fromAvId):
        senderId = self.air.getAvatarIdFromSender()
        if toAvId != self.doId:
            self.air.writeServerEvent('suspicious', self.doId, 'toAvId=%d is not equal to self.doId' % toAvId)
            return
        if available != 1:
            self.air.writeServerEvent('suspicious', self.doId, 'invalid availableValue=%d' % available)
            return
        if fromAvId == 0:
            return
        self.air.teleportRegistrar.registerValidTeleport(toAvId, available, shardId, hoodId, zoneId, fromAvId)
        dg = self.dclass.aiFormatUpdate('teleportResponse', fromAvId, fromAvId, self.doId, [toAvId,
         available,
         shardId,
         hoodId,
         zoneId])
        self.air.send(dg)

    def b_setGM(self, type):
        self.sendUpdate('setGM', [type])
        self.setGM(type)

    def setGM(self, type):
        wasGM = self._isGM
        formerType = self._gmType
        self._isGM = type != 0
        self._gmType = None
        if self._isGM:
            self._gmType = type - 1
            MaxGMType = 5
            if self._gmType > MaxGMType:
                self.notify.warning('toon %s has invalid GM type: %s' % (self.doId, self._gmType))
                self._gmType = MaxGMType
        return

    def isGM(self):
        return self._isGM

    def _updateGMName(self, formerType = None):
        if formerType is None:
            formerType = self._gmType
        name = self.name
        if formerType is not None:
            gmPrefix = TTLocalizer.GM_NAMES[formerType] + ' '
            if self._nameIsPrefixed(gmPrefix):
                name = self.name[len(gmPrefix):]
        if self._isGM:
            gmPrefix = TTLocalizer.GM_NAMES[self._gmType] + ' '
            newName = gmPrefix + name
        else:
            newName = name
        if self.name != newName:
            self.b_setName(newName)
        return

    def _handleGMName(self):
        name = self.name
        self.setDisplayName(name)
        if self._isGM:
            self.setNametagStyle(0)
            self.setGMIcon(self._gmType)
            self.gmToonLockStyle = True
        else:
            self.gmToonLockStyle = False
            self.removeGMIcon()
            self.setNametagStyle(0)

    def setGMIcon(self, gmType = None):
        if hasattr(self, 'gmIcon') and self.gmIcon:
            return

        modelName = 'phase_3.5/models/gui/tt_m_gui_gm_accesslvl_%s.bam'
        al = (103, 502, 504, 508, 701)

        access = self._gmType
        if access >= len(al):
            return

        self.gmIcon = loader.loadModel(modelName % al[access])
        self.gmIcon.setScale(5.25)
        np = NodePath(self.nametag.getNameIcon())
        self.gmIcon.reparentTo(np)
        self.setTrophyScore(self.trophyScore)
        self.gmIcon.setZ(-2.5)
        self.gmIcon.setY(0.0)
        self.gmIcon.setColor(Vec4(1.0, 1.0, 1.0, 1.0))
        self.gmIcon.setTransparency(1)
        self.gmIconInterval = LerpHprInterval(self.gmIcon, 3.0, Point3(0, 0, 0), Point3(-360, 0, 0))
        self.gmIconInterval.loop()

        self.gmIcon.find('**/gmPartyHat').removeNode()

    def setGMPartyIcon(self):
        gmType = self._gmType
        iconInfo = ('phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist', 'phase_3.5/models/gui/tt_m_gui_gm_toontroop_whistle', 'phase_3.5/models/gui/tt_m_gui_gm_toonResistance_fist', 'phase_3.5/models/gui/tt_m_gui_gm_toontroop_getConnected')
        if gmType > len(iconInfo) - 1:
            return
        self.gmIcon = loader.loadModel(iconInfo[gmType])
        self.gmIcon.reparentTo(NodePath(self.nametag.getNameIcon()))
        self.gmIcon.setScale(3.25)
        self.setTrophyScore(self.trophyScore)
        self.gmIcon.setZ(1.0)
        self.gmIcon.setY(0.0)
        self.gmIcon.setColor(Vec4(1.0, 1.0, 1.0, 1.0))
        self.gmIcon.setTransparency(1)
        self.gmIconInterval = LerpHprInterval(self.gmIcon, 3.0, Point3(0, 0, 0), Point3(-360, 0, 0))
        self.gmIconInterval.loop()

    def removeGMIcon(self):
        if hasattr(self, 'gmIconInterval') and self.gmIconInterval:
            self.gmIconInterval.finish()
            del self.gmIconInterval
        if hasattr(self, 'gmIcon') and self.gmIcon:
            self.gmIcon.detachNode()
            del self.gmIcon

    @staticmethod
    def staticGetLogicalZoneChangeAllEvent():
        return 'DOLogicalChangeZone-all'

    def handleHacking(self, response, comment, coconspirators = []):
        if response == 'quietzone':
            self.b_setLocation(self.parentId, ToontownGlobals.QuietZone)
        elif response == 'disconnect':
            self.disconnect()
        elif response == 'disconnectall':
            self.disconnect()
            for coconspirator in coconspirators:
                coconspirator.disconnect()

        elif response == 'ban':
            self.ban('collision and position hacking')
            self.disconnect()
        elif response == 'banall':
            self.ban('collision and position hacking')
            self.disconnect()
            for coconspirator in coconspirators:
                coconspirator.ban('collision and position hacking')
                coconspirator.disconnect()

    def setAnimalSound(self, index):
        self.animalSound = index

    def d_setAnimalSound(self, index):
        self.sendUpdate('setAnimalSound', [index])

    def b_setAnimalSound(self, index):
        self.setAnimalSound(index)
        self.d_setAnimalSound(index)

    def getAnimalSound(self):
        return self.animalSound

    def addBuff(self, id, duration):
        buffCount = len(self.buffs)
        if buffCount <= id:
            self.buffs.extend([0] * ((id+1) - buffCount))
        timestamp = int(time.time()) + (duration*60)
        self.buffs[id] = timestamp
        self.b_setBuffs(self.buffs)

    def removeBuff(self, id):
        if len(self.buffs) <= id:
            self.notify.warning('tried to remove non-existent buff %d on avatar %d.' % (id, self.doId))
            return
        self.buffs[id] = 0
        self.d_setBuffs(self.buffs)

    def hasBuff(self, id):
        if len(self.buffs) <= id:
            return False
        return self.buffs[id] != 0

    def setBuffs(self, buffs):
        self.buffs = buffs
        for id, timestamp in enumerate(self.buffs):
            if timestamp:
                taskName = self.uniqueName('removeBuff-%s' % id)
                taskMgr.remove(taskName)
                delayTime = max(timestamp - int(time.time()), 0)
                taskMgr.doMethodLater(delayTime, self.removeBuff, taskName, extraArgs=[id])

    def d_setBuffs(self, buffs):
        self.sendUpdate('setBuffs', [buffs])

    def b_setBuffs(self, buffs):
        self.setBuffs(buffs)
        self.d_setBuffs(buffs)

    def setRedeemedCodes(self, redeemedCodes):
        self.redeemedCodes = redeemedCodes

    def d_setRedeemedCodes(self, redeemedCodes):
        self.sendUpdate('setRedeemedCodes', [redeemedCodes])

    def b_setRedeemedCodes(self, redeemedCodes):
        self.setRedeemedCodes(redeemedCodes)
        self.d_setRedeemedCodes(redeemedCodes)

    def getRedeemedCodes(self, redeemedCodes):
        return self.redeemedCodes

    def isCodeRedeemed(self, code):
        return code in self.redeemedCodes

    def redeemCode(self, code):
        if not self.isCodeRedeemed(code):
            self.redeemedCodes.append(code)
            self.b_setRedeemedCodes(self.redeemedCodes)

    def removeCode(self, code):
        if self.isCodeRedeemed(code):
            self.redeemedCodes.remove(code)
            self.b_setRedeemedCodes(self.redeemedCodes)

    def setTrueFriends(self, trueFriends):
        self.trueFriends = trueFriends

    def d_setTrueFriends(self, trueFriends):
        self.sendUpdate('setTrueFriends', [trueFriends])

    def b_setTrueFriends(self, trueFriends):
        self.setTrueFriends(trueFriends)
        self.d_setTrueFriends(trueFriends)

    def isTrueFriends(self, avId):
        return avId in self.trueFriends

    def addTrueFriend(self, avId):
        if avId in self.trueFriends:
            return

        self.trueFriends.append(avId)
        self.b_setTrueFriends(self.trueFriends)

    def getTrueFriends(self, trueFriends):
        return self.trueFriends

    def setNextKnockHeal(self, nextKnockHeal):
        self.nextKnockHeal = nextKnockHeal

    def d_setNextKnockHeal(self, nextKnockHeal):
        self.sendUpdate('setNextKnockHeal', [nextKnockHeal])

    def b_setNextKnockHeal(self, nextKnockHeal):
        self.setNextKnockHeal(nextKnockHeal)
        self.d_setNextKnockHeal(nextKnockHeal)

    def getNextKnockHeal(self):
        return self.nextKnockHeal

    def setTFRequest(self, tfRequest):
        self.tfRequest = tfRequest

    def d_setTFRequest(self, tfRequest):
        self.sendUpdate('setTFRequest', [tfRequest])

    def b_setTFRequest(self, tfRequest):
        self.setTFRequest(tfRequest)
        self.d_setTFRequest(tfRequest)

    def getTFRequest(self):
        return self.tfRequest

    def setEPP(self, epp):
        self.epp = epp

    def d_setEPP(self, epp):
        self.sendUpdate("setEPP", [epp])

    def b_setEPP(self, epp):
        self.setEPP(epp)
        self.d_setEPP(epp)

    def addEPP(self, dept):
        self.epp.append(dept)
        self.d_setEPP(self.epp)

    def removeEPP(self, dept):
        if dept in self.epp:
            self.epp.remove(dept)

        self.d_setEPP(self.epp)

    def hasEPP(self, dept):
        return dept in self.epp

# Exp command

    def b_setExperience(self, experience):
        self.d_setExperience(experience)
        self.setExperience(experience)

    def d_setExperience(self, experience):
        self.sendUpdate('setExperience', [experience])

    def setExperience(self, experience):
        self.experience = Experience.Experience(experience, self)

    def getExperience(self):
        return self.experience.makeNetString()

@magicWord(category=CATEGORY_STAFF, types=[str, int, int])
def cheesyEffect(value, hood=0, expire=0):
    """
    Modify the target's cheesy effect.
    """
    try:
        value = int(value)
    except:
        value = value.lower()
    if isinstance(value, str):
        if value not in OTPGlobals.CEName2Id:
            return 'Invalid cheesy effect value: %s' % value
        value = OTPGlobals.CEName2Id[value]
    elif not 0 <= value <= 15:
        return 'Invalid cheesy effect value: %d' % value
    if (hood != 0) and (not 1000 <= hood < ToontownGlobals.DynamicZonesBegin):
        return 'Invalid hood ID: %d' % hood
    target = spellbook.getTarget()
    target.b_setCheesyEffect(value, hood, expire)
    return 'Set %s\'s cheesy effect to: %d' % (target.getName(), value)

@magicWord(category=CATEGORY_STAFF, types=[int])
def hp(hp):
    """
    Modify the target's current HP.
    """
    target = spellbook.getTarget()
    maxHp = target.getMaxHp()
    if not -1 <= hp <= maxHp:
        return 'HP must be in range (-1-%d).' % maxHp
    target.b_setHp(hp)
    return 'Set your HP to: %d' % hp

@magicWord(category=CATEGORY_STAFF, types=[int])
def maxHp(maxHp):
    """
    Modify the invoker's max HP.
    """
    if not 15 <= maxHp <= ToontownGlobals.MaxHpLimit:
        return 'HP must be in range (15-%d).' % ToontownGlobals.MaxHpLimit
    invoker = spellbook.getTarget()
    invoker.b_setHp(maxHp)
    invoker.b_setMaxHp(maxHp)
    invoker.toonUp(maxHp - invoker.getHp())
    return 'Set your max HP to: %d' % maxHp

@magicWord(category=CATEGORY_LEADER, types=[str])
def textColor(color):
    """
    Modify the target's text color.
    """
    spellbook.getTarget().b_setTextColor(color)
    return 'Set your color to: %s' % color

@magicWord(category=CATEGORY_STAFF, types=[str])
def allSummons():
    """
    Max the target's summons
    """
    target = spellbook.getTarget()

    numSuits = len(SuitDNA.suitHeadTypes)
    fullSetForSuit = 1 | 2 | 4 | 8 | 16 | 32
    allSummons = numSuits * [fullSetForSuit]
    target.b_setCogSummonsEarned(allSummons)
    return 'Lots of summons!'

@magicWord(category=CATEGORY_STAFF, types=[str])
def maxToon(missingTrack=None):
    """
    Max the target's stats for end-level gameplay.
    """
    target = spellbook.getTarget()

    # First, unlock the target's Gag tracks:
    gagTracks = [1, 1, 1, 1, 1, 1, 1]
    if missingTrack is not None:
        try:
            index = ('toonup', 'trap', 'lure', 'sound', 'throw',
                     'squirt', 'drop').index(missingTrack)
        except:
            return 'Missing Gag track is invalid!'
        if index in (4, 5):
            return 'You are required to have Throw and Squirt.'
        gagTracks[index] = 0
    target.b_setTrackAccess(gagTracks)
    target.b_setMaxCarry(80)

    # Next, max out their experience for the tracks they have:
    experience = Experience.Experience(target.getExperience(), target)
    for i, track in enumerate(target.getTrackAccess()):
        if track:
            experience.experience[i] = (
                Experience.MaxSkill - Experience.UberSkill)
    target.b_setExperience(experience.makeNetString())

    # Max out their Laff:
    target.b_setMaxHp(ToontownGlobals.MaxHpLimit)
    target.toonUp(target.getMaxHp() - target.hp)

    # Unlock all of the emotes:
    emotes = list(target.getEmoteAccess())
    for emoteId in OTPLocalizer.EmoteFuncDict.values():
        if emoteId >= len(emotes):
            continue
        # The following emotions are ignored because they are unable to be
        # obtained:
        if emoteId in (17, 18, 19):
            continue
        emotes[emoteId] = 1
    target.b_setEmoteAccess(emotes)

    # Max out their Cog suits:
    target.b_setCogParts(
        [
            CogDisguiseGlobals.PartsPerSuitBitmasks[0],  # Bossbot
            CogDisguiseGlobals.PartsPerSuitBitmasks[1],  # Lawbot
            CogDisguiseGlobals.PartsPerSuitBitmasks[2],  # Cashbot
            CogDisguiseGlobals.PartsPerSuitBitmasks[3]   # Sellbot
        ]
    )
    target.b_setCogLevels([49] * 4)
    target.b_setCogTypes([7, 7, 7, 7])

    # Max their Cog gallery:
    deptCount = len(SuitDNA.suitDepts)
    target.b_setCogCount(list(CogPageGlobals.COG_QUOTAS[1]) * deptCount)
    cogStatus = [CogPageGlobals.COG_COMPLETE2] * SuitDNA.suitsPerDept
    target.b_setCogStatus(cogStatus * deptCount)
    target.b_setCogRadar([1, 1, 1, 1])
    target.b_setBuildingRadar([1, 1, 1, 1])

    # Max out their racing tickets:
    target.b_setTickets(99999)

    # Give them teleport access everywhere (including Cog HQs):
    hoods = list(ToontownGlobals.HoodsForTeleportAll)
    target.b_setHoodsVisited(hoods)
    target.b_setTeleportAccess(hoods)

    # Max their quest carry limit:
    target.b_setQuestCarryLimit(4)

    # Complete their quests:
    target.b_setQuests([])
    target.b_setRewardHistory(Quests.ELDER_TIER, [])

    # Max their money:
    target.b_setMaxMoney(250)
    target.b_setMaxBankMoney(30000)
    target.b_setMoney(target.getMaxMoney())
    target.b_setBankMoney(target.getMaxBankMoney())

    # Finally, unlock all of their pet phrases:
    if simbase.wantPets:
        target.b_setPetTrickPhrases(range(7))

    return 'Maxed your Toon!'

@magicWord(category=CATEGORY_STAFF, types=[int, str])
def sos(count, name):
    """
    Modifies the target's specified SOS card count.
    """
    target = spellbook.getTarget()
    if not 0 <= count <= 100:
        return 'Your SOS count must be in range (0-100).'
    for npcId, npcName in TTLocalizer.NPCToonNames.items():
        if name.lower() == npcName.lower():
            if npcId not in NPCToons.npcFriends:
                continue
            break
    else:
        return 'SOS card %s was not found!' % name
    if (count == 0) and (npcId in target.NPCFriendsDict):
        del target.NPCFriendsDict[npcId]
    else:
        target.NPCFriendsDict[npcId] = count
    target.d_setNPCFriendsDict(target.NPCFriendsDict)
    return "%s was given %d %s SOS cards." % (target.getName(), count, name)

@magicWord(category=CATEGORY_STAFF, types=[int])
def unites(value=32767):
    """
    Restock all resistance messages.
    """
    target = spellbook.getTarget()
    value = min(value, 32767)
    target.restockAllResistanceMessages(value)
    return 'Restocked %d unites for %s!' % (value, target.getName())

@magicWord(category=CATEGORY_STAFF, types=[int])
def fires(count):
    """
    Modifies the target's pink slip count.
    """
    target = spellbook.getTarget()
    if not 0 <= count <= 255:
        return 'Your fire count must be in range (0-255).'
    target.b_setPinkSlips(count)
    return '%s was given %d fires.' % (target.getName(), count)

@magicWord(category=CATEGORY_LEADER, types=[int])
def crateKeys(count):
    """
    Modifies the invoker's crate key count.
    """
    target = spellbook.getTarget()
    if not 0 <= count <= 255:
        return 'Your crate key must be in range (0-255).'
    target.b_setCrateKeys(count)
    return 'You were given %d crate keys.' % count

@magicWord(category=CATEGORY_STAFF, types=[int])
def maxMoney(maxMoney):
    """
    Modifies the target's max money value.
    """
    if not 40 <= maxMoney <= 250:
        return 'Max money value must be in xrange (40-250).'
    target = spellbook.getTarget()
    spellbook.getTarget().b_setMaxMoney(maxMoney)
    return "Set {0}'s max money value to {1}!".format(target.getName(), maxMoney)

@magicWord(category=CATEGORY_STAFF, types=[int])
def maxBankMoney(maxBankMoney):
    """
    Modifies the target's max bank money value.
    """

    if not 10000 <= maxBankMoney <= 30000:
        return 'Max bank money value must be in xrange (10000-30000).'
    target = spellbook.getTarget()
    spellbook.getTarget().b_setMaxBankMoney(maxBankMoney)
    return "Set {0}'s max bank money value to {1}!".format(target.getName(), maxBankMoney)

@magicWord(category=CATEGORY_STAFF, types=[int])
def money(money):
    """
    Modifies the target's current money value.
    """
    target = spellbook.getTarget()
    maxMoney = target.getMaxMoney()
    if not 0 <= money <= maxMoney:
        return 'Money value must be in xrange (0-%d).' % maxMoney
    target.b_setMoney(money)
    return "Set %s's money value to %d!" % (target.getName(), money)

@magicWord(category=CATEGORY_STAFF, types=[int])
def bank(money):
    """
    Modifies the target's current bank money value.
    """
    target = spellbook.getTarget()
    maxMoney = target.getMaxBankMoney()

    if not 0 <= money <= maxMoney:
        return 'Bank money must be in xrange (0-%d.)' % maxMoney
    target.b_setBankMoney(money)
    return "Set %s's bank money value to %d!" % (target.getName(), money)

@magicWord(category=CATEGORY_STAFF, types=[int])
def fishingRod(rod):
    """
    Modify the target's fishing rod value.
    """
    if not 0 <= rod <= 4:
        return 'Rod value must be in xrange (0-4).'
    target = spellbook.getTarget()
    target.b_setFishingRod(rod)
    target.b_setMaxFishingRod(rod)
    return "Set %s's fishing rod to %d!" % (target.getName(), rod)

@magicWord(category=CATEGORY_STAFF, types=[int])
def maxFishTank(maxFishTank):
    """
    Modify the target's max fish tank value.
    """
    if not 20 <= maxFishTank <= FishGlobals.MaxTank:
        return 'Max fish tank value must be in xrange (20-%s).' % FishGlobals.MaxTank
    target = spellbook.getTarget()
    target.b_setMaxFishTank(maxFishTank)
    return "Set %s's max fish tank value to %d!" % (target.getName(), maxFishTank)

@magicWord(category=CATEGORY_STAFF, types=[str])
def name(name=''):
    """
    Modify the target's name.
    """
    target = spellbook.getTarget()
    _name = target.getName()
    target.b_setName(name)
    if name:
        return "Set %s's name to %s!" % (_name, name)
    else:
        return "%s's name is now empty!" % _name

@magicWord(category=CATEGORY_STAFF, types=[int])
def squish(laff):
    """
    Squish a toon.
    """
    target = spellbook.getTarget()
    target.squish(laff)

@magicWord(category=CATEGORY_STAFF, types=[int, int])
def hat(hatIndex, hatTex=0):
    """
    Modify the target's hat.
    """
    if not 0 <= hatIndex < len(ToonDNA.HatModels):
        return 'Invalid hat index.'
    if not 0 <= hatTex < len(ToonDNA.HatTextures):
        return 'Invalid hat texture.'
    target = spellbook.getTarget()
    target.b_setHat(hatIndex, hatTex, 0)
    return "Set %s's hat to %d, %d!" % (target.getName(), hatIndex, hatTex)

@magicWord(category=CATEGORY_STAFF, types=[int, int])
def glasses(glassesIndex, glassesTex=0):
    """
    Modify the target's glasses.
    """
    if not 0 <= glassesIndex < len(ToonDNA.GlassesModels):
        return 'Invalid glasses index.'
    if not 0 <= glassesTex < len(ToonDNA.GlassesTextures):
        return 'Invalid glasses texture.'
    target = spellbook.getTarget()
    target.b_setGlasses(glassesIndex, glassesTex, 0)
    return "Set %s's glasses to %d, %d!" % (target.getName(), glassesIndex, glassesTex)

@magicWord(category=CATEGORY_STAFF, types=[int, int])
def backpack(backpackIndex, backpackTex=0):
    """
    Modify the target's backpack.
    """
    if not 0 <= backpackIndex < len(ToonDNA.BackpackModels):
        return 'Invalid backpack index.'
    if not 0 <= backpackTex < len(ToonDNA.BackpackTextures):
        return 'Invalid backpack texture.'
    target = spellbook.getTarget()
    target.b_setBackpack(backpackIndex, backpackTex, 0)
    return "Set %s's backpack to %d, %d!" % (target.getName(), backpackIndex, backpackTex)

@magicWord(category=CATEGORY_STAFF, types=[int, int])
def shoes(shoesIndex, shoesTex=0):
    """
    Modify the target's shoes.
    """
    if not 0 <= shoesIndex < len(ToonDNA.ShoesModels):
        return 'Invalid shoes index.'
    if not 0 <= shoesTex < len(ToonDNA.ShoesTextures):
        return 'Invalid shoes texture.'
    target = spellbook.getTarget()
    target.b_setShoes(shoesIndex, shoesTex, 0)
    return "Set %s's shoes to %d, %d!" % (target.getName(), shoesIndex, shoesTex)

@magicWord(category=CATEGORY_TRIAL)
def ghost():
    """
    Toggles invisibility on the invoker. Anyone with an access level below the
    invoker will not be able to see him or her.
    """
    invoker = spellbook.getInvoker()
    if invoker.ghostMode == 0:
        invoker.b_setGhostMode(2)
        return 'Ghost mode is enabled.'
    else:
        invoker.b_setGhostMode(0)
        return 'Ghost mode is disabled.'

@magicWord(category=CATEGORY_STAFF)
def badName():
    """
    Revoke the target's name.
    """
    target = spellbook.getTarget()
    _name = target.getName()
    colorString = TTLocalizer.ColorfulToon
    animalType = TTLocalizer.AnimalToSpecies[target.dna.getAnimal()]
    target.b_setName(colorString + ' ' + animalType)
    target.sendUpdate('setWishNameState', ['REJECTED'])
    return "Revoked %s's name!" % _name

@magicWord(category=CATEGORY_STAFF, types=[int])
def tickets(tickets):
    """
    Set the invoker's racing tickets value.
    """
    if not 0 <= tickets <= 99999:
        return 'Racing tickets value must be in range (0-99999).'
    invoker = spellbook.getInvoker()
    invoker.b_setTickets(tickets)
    return 'Set your tickets to: %d' % tickets

@magicWord(category=CATEGORY_STAFF, types=[int])
def cogIndex(index):
    """
    Modifies the invoker's Cog index.
    """
    if not -1 <= index <= 3:
        return 'Invalid Cog index.'
    invoker = spellbook.getInvoker()
    invoker.b_setCogIndex(index)
    return 'Set your Cog index to %d!' % index

@magicWord(category=CATEGORY_STAFF, types=[str, int, int])
def inventory(a, b=None, c=None):
    target = spellbook.getTarget()
    inventory = target.inventory
    if a == 'reset':
        maxLevelIndex = b or 5
        if not 0 <= maxLevelIndex < len(ToontownBattleGlobals.Levels[0]):
            return 'Invalid max level index: ' + str(maxLevelIndex)
        targetTrack = -1 or c
        if not -1 <= targetTrack < len(ToontownBattleGlobals.Tracks):
            return 'Invalid target track index: ' + str(targetTrack)
        for track in xrange(0, len(ToontownBattleGlobals.Tracks)):
            if (targetTrack == -1) or (track == targetTrack):
                inventory.inventory[track][:maxLevelIndex + 1] = [0] * (maxLevelIndex+1)
        target.b_setInventory(inventory.makeNetString())
        if targetTrack == -1:
            return 'Inventory reset.'
        else:
            return 'Inventory reset for target track index: ' + str(targetTrack)
    elif a == 'restock':
        maxLevelIndex = b or 5
        if not 0 <= maxLevelIndex < len(ToontownBattleGlobals.Levels[0]):
            return 'Invalid max level index: ' + str(maxLevelIndex)
        targetTrack = -1 or c
        if not -1 <= targetTrack < len(ToontownBattleGlobals.Tracks):
            return 'Invalid target track index: ' + str(targetTrack)
        if (targetTrack != -1) and (not target.hasTrackAccess(targetTrack)):
            return "You don't have target track index: " + str(targetTrack)
        inventory.NPCMaxOutInv(targetTrack=targetTrack, maxLevelIndex=maxLevelIndex)
        target.b_setInventory(inventory.makeNetString())
        if targetTrack == -1:
            return 'Inventory restocked.'
        else:
            return 'Inventory restocked for target track index: ' + str(targetTrack)
    else:
        try:
            targetTrack = int(a)
        except:
            return 'Invalid first argument.'
        if not target.hasTrackAccess(targetTrack):
            return "You don't have target track index: " + str(targetTrack)
        maxLevelIndex = b or 6
        if not 0 <= maxLevelIndex < len(ToontownBattleGlobals.Levels[0]):
            return 'Invalid max level index: ' + str(maxLevelIndex)
        for _ in xrange(c):
            inventory.addItem(targetTrack, maxLevelIndex)
        target.b_setInventory(inventory.makeNetString())
        return 'Restored %d Gags to: %d, %d' % (c, targetTrack, maxLevelIndex)

@magicWord(category=CATEGORY_STAFF, types=[str, str])
def dna(part, value):
    """Modify a DNA part on the target."""
    target = spellbook.getTarget()

    dna = ToonDNA.ToonDNA()
    dna.makeFromNetString(target.getDNAString())

    part = part.lower()
    if part.endswith('color') or part.endswith('tex') or part.endswith('size'):
        value = int(value)

    if part == 'gender':
        if value not in ('m', 'f', 'male', 'female'):
            return 'Invalid gender: ' + value
        dna.gender = value[0]
        target.b_setDNAString(dna.makeNetString())
        return 'Gender set to: ' + dna.gender

    if part in ('head', 'species'):
        speciesNames = (
            'dog', 'cat', 'horse', 'mouse', 'rabbit', 'duck', 'monkey', 'bear',
            'pig'
        )
        if value in speciesNames:
            speciesIndex = speciesNames.index(value)
            value = ToonDNA.toonSpeciesTypes[speciesIndex]
        if value not in ToonDNA.toonSpeciesTypes:
            return 'Invalid species: ' + value
        dna.head = value + dna.head[1:3]
        target.b_setDNAString(dna.makeNetString())
        return 'Species set to: ' + dna.head[0]

    if part == 'headsize':
        sizes = ('ls', 'ss', 'sl', 'll')
        if not 0 <= value <= len(sizes):
            return 'Invalid head size index: ' + str(value)
        dna.head = dna.head[0] + sizes[value]
        target.b_setDNAString(dna.makeNetString())
        return 'Head size index set to: ' + dna.head[1:]

    if part == 'torso':
        if dna.gender not in ('m', 'f'):
            return 'Unknown gender.'
        value = int(value)
        if (dna.gender == 'm') and (not 0 <= value <= 2):
            return 'Male torso index out of range (0-2).'
        if (dna.gender == 'f') and (not 3 <= value <= 8):
            return 'Female torso index out of range (3-8).'
        dna.torso = ToonDNA.toonTorsoTypes[value]
        target.b_setDNAString(dna.makeNetString())
        return 'Torso set to: ' + dna.torso

    if part == 'legs':
        value = int(value)
        if not 0 <= value <= len(ToonDNA.toonLegTypes):
            return 'Legs index out of range (0-%d).' % len(ToonDNA.toonLegTypes)
        dna.legs = ToonDNA.toonLegTypes[value]
        target.b_setDNAString(dna.makeNetString())
        return 'Legs set to: ' + dna.legs

    if part == 'headcolor':
        if value not in ToonDNA.defaultColorList:
            return 'Invalid head color index: ' + str(value)
        dna.headColor = value
        target.b_setDNAString(dna.makeNetString())
        return 'Head color index set to: ' + str(dna.headColor)

    if part == 'armcolor':
        if value not in ToonDNA.defaultColorList:
            return 'Invalid arm color index: ' + str(value)
        dna.armColor = value
        target.b_setDNAString(dna.makeNetString())
        return 'Arm color index set to: ' + str(dna.armColor)

    if part == 'legcolor':
        if value not in ToonDNA.defaultColorList:
            return 'Invalid leg color index: ' + str(value)
        dna.legColor = value
        target.b_setDNAString(dna.makeNetString())
        return 'Leg color index set to: ' + str(dna.legColor)

    if part == 'color':
        if (value not in ToonDNA.defaultColorList) and (value != 0x1a) and (value != 0x00):
            return 'Invalid color index: ' + str(value)
        if (value == 0x1a) and (dna.getAnimal() != 'cat'):
            return 'Invalid color index for species: ' + dna.getAnimal()
        if (value == 0x00) and (dna.getAnimal() != 'bear'):
            return 'Invalid color index for species: ' + dna.getAnimal()
        dna.headColor = value
        dna.armColor = value
        dna.legColor = value
        target.b_setDNAString(dna.makeNetString())
        return 'Color index set to: ' + str(dna.headColor)

    if part == 'gloves':
        value = int(value)
        dna.gloveColor = value
        target.b_setDNAString(dna.makeNetString())
        return 'Glove color set to: ' + str(dna.gloveColor)

    if part == 'toptex':
        if not 0 <= value <= len(ToonDNA.Shirts):
            return 'Top texture index out of range (0-%d).' % len(ToonDNA.Shirts)
        dna.topTex = value
        target.b_setDNAString(dna.makeNetString())
        return 'Top texture index set to: ' + str(dna.topTex)

    if part == 'toptexcolor':
        if not 0 <= value <= len(ToonDNA.ClothesColors):
            return 'Top texture color index out of range(0-%d).' % len(ToonDNA.ClothesColors)
        dna.topTexColor = value
        target.b_setDNAString(dna.makeNetString())
        return 'Top texture color index set to: ' + str(dna.topTexColor)

    if part == 'sleevetex':
        if not 0 <= value <= len(ToonDNA.Sleeves):
            return 'Sleeve texture index out of range(0-%d).' % len(ToonDNA.Sleeves)
        dna.sleeveTex = value
        target.b_setDNAString(dna.makeNetString())
        return 'Sleeve texture index set to: ' + str(dna.sleeveTex)

    if part == 'sleevetexcolor':
        if not 0 <= value <= len(ToonDNA.ClothesColors):
            return 'Sleeve texture color index out of range(0-%d).' % len(ToonDNA.ClothesColors)
        dna.sleeveTexColor = value
        target.b_setDNAString(dna.makeNetString())
        return 'Sleeve texture color index set to: ' + str(dna.sleeveTexColor)

    if part == 'bottex':
        if dna.gender not in ('m', 'f'):
            return 'Unknown gender.'
        if dna.gender == 'm':
            bottoms = ToonDNA.BoyShorts
        else:
            bottoms = ToonDNA.GirlBottoms
        if not 0 <= value <= len(bottoms):
            return 'Bottom texture index out of range (0-%d).' % len(bottoms)
        dna.botTex = value
        target.b_setDNAString(dna.makeNetString())
        return 'Bottom texture index set to: ' + str(dna.botTex)

    if part == 'bottexcolor':
        if not 0 <= value <= len(ToonDNA.ClothesColors):
            return 'Bottom texture color index out of range(0-%d).' % len(ToonDNA.ClothesColors)
        dna.botTexColor = value
        target.b_setDNAString(dna.makeNetString())
        return 'Bottom texture color index set to: ' + str(dna.botTexColor)

    if part == 'show':
        return dna.asNpcTuple() if value else dna.asTuple()
    if part == 'showrandom':
        return NPCToons.getRandomDNA(time.time(), value)
    return 'Invalid part: ' + part

@magicWord(category=CATEGORY_LEADER, types=[int])
def trophyScore(value):
    """
    Modifies the target's trophy score.
    """
    if value < 0:
        return 'Invalid trophy score: ' + str(value)
    target = spellbook.getTarget()
    simbase.air.trophyMgr.updateTrophyScore(target.doId, value)
    return "%s's trophy score has been set to: %d" % (target.getName(), value)

@magicWord(category=CATEGORY_STAFF, types=[int, int])
def givePies(pieType, numPies=0):
    """
    Give the target (numPies) of (pieType) pies.
    """
    target = spellbook.getTarget()
    if pieType == -1:
        target.b_setNumPies(0)
        return "Removed %s's pies." % target.getName()
    if not 0 <= pieType <= 7:
        return 'Pie type must be in range (0-7).'
    if not -1 <= numPies <= 99:
        return 'Pie count out of range (-1-99).'
    target.b_setPieType(pieType)
    if numPies >= 0:
        target.b_setNumPies(numPies)
    else:
        target.b_setNumPies(ToontownGlobals.FullPies)

@magicWord(category=CATEGORY_STAFF, types=[int, int])
def trackBonus(trackIndex, level):
    """
    Modify the invoker's track bonus level.
    """
    invoker = spellbook.getInvoker()
    if not 0 <= trackIndex < 7:
        return 'Invalid track index!'
    if not -1 <= level <= 6:
        return 'Invalid level!'
    trackBonusLevel = [0] * 7
    trackBonusLevel[trackIndex] = level
    invoker.b_setTrackBonusLevel(trackBonusLevel)
    return 'Your track bonus level has been set to %s!' % level

@magicWord(category=CATEGORY_STAFF, types=[str, str, int])
def track(command, track, value=None):
    try:
        index = ('toonup', 'trap', 'lure', 'sound', 'throw',
                 'squirt', 'drop').index(track.lower())
    except:
        return 'Invalid Gag track!'
    invoker = spellbook.getInvoker()
    trackAccess = invoker.getTrackAccess()
    if (command.lower() not in ('add',)) and (not trackAccess[index]):
        return "You don't have that track!"
    if command.lower() == 'remove':
        if index in (4, 5):
            return "You can't remove throw and squirt!"
        trackAccess[index] = 0
        invoker.b_setTrackAccess(trackAccess)
        return 'Removed the %s track!' % track
    if command.lower() == 'add':
        trackAccess[index] = 1
        invoker.b_setTrackAccess(trackAccess)
        return 'Added the %s track!' % track
    if command.lower() == 'experience':
        if value is None:
            return 'You must provide an experience value.'
        if not 0 <= value <= Experience.MaxSkill:
            return 'Experience value not in xrange (0-%d).' % Experience.MaxSkill
        experience = Experience.Experience(invoker.getExperience(), invoker)
        experience.experience[index] = value
        invoker.b_setExperience(experience.makeNetString())
        return 'Set the experience of the %s track to: %d!' % (track, value)
    return 'Invalid command.'

@magicWord(category=CATEGORY_STAFF, types=[str, str])
def suit(command, suitName = 'f'):
    invoker = spellbook.getInvoker()
    command = command.lower()
    if suitName not in SuitDNA.suitHeadTypes:
        return 'Invalid suit name: ' + suitName
    suitFullName = SuitBattleGlobals.SuitAttributes[suitName]['name']
    if command == 'spawn':
        returnCode = invoker.doSummonSingleCog(SuitDNA.suitHeadTypes.index(suitName))
        if returnCode[0] == 'success':
            return 'Successfully spawned: ' + suitFullName
        return "Couldn't spawn: " + suitFullName
    elif command == 'building':
        returnCode = invoker.doBuildingTakeover(SuitDNA.suitHeadTypes.index(suitName))
        if returnCode[0] == 'success':
            return 'Successfully spawned a Cog building with: ' + suitFullName
        return "Couldn't spawn a Cog building with: " + suitFullName
    elif command == 'nobuilding':
        returnCode = invoker.doToonBuildingTakeover()
        if returnCode[0] == 'success':
            return 'Toons took over the cog building!'
        return "Couldn't allow toons to take over cog building because " + returnCode[1]
    else:
        return 'Invalid command.'

@magicWord(category=CATEGORY_DEVELOPER)
def getZone():
    invoker = spellbook.getInvoker()
    zone = invoker.zoneId
    return 'ZoneID: %s' % (zone)

@magicWord(category=CATEGORY_STAFF, types=[int])
def nametagStyle(nametagStyle):
    if nametagStyle >= len(TTLocalizer.NametagFontNames):
        return 'Invalid nametag style.'
    target = spellbook.getTarget()
    target.b_setNametagStyle(nametagStyle)
    target.addNametagStyle(nametagStyle)
    return 'Nametag style set to: %s.' % TTLocalizer.NametagFontNames[nametagStyle]

@magicWord(category=CATEGORY_DEVELOPER, types=[str, int, int])
def disguise(command, suitIndex, value):
    invoker = spellbook.getInvoker()

    if suitIndex > 3:
        return 'Invalid suit index: %s' % suitIndex
    if value < 0:
        return 'Invalid value: %s' % value

    if command == 'parts':
        invoker.cogParts[suitIndex] = 0
        for _ in xrange(value):
            invoker.giveGenericCogPart('fullSuit', suitIndex)
        return 'Parts set.'
    elif command == 'tier':
        invoker.cogTypes[suitIndex] = value
        invoker.d_setCogTypes(invoker.cogTypes)
        return 'Tier set.'
    elif command == 'level':
        invoker.cogLevels[suitIndex] = value
        invoker.d_setCogLevels(invoker.cogLevels)
        return 'Level set.'
    elif command == 'merits':
        invoker.cogMerits[suitIndex] = value
        invoker.d_setCogMerits(invoker.cogMerits)
        return 'Merits set.'
    else:
        return 'Unknow command: %s' % command

@magicWord(category=CATEGORY_LEADER)
def unlimitedGags():
    """ Restock avatar's gags at the start of each round. """
    av = spellbook.getTarget() if spellbook.getInvokerAccess() >= 500 else spellbook.getInvoker()
    av.setUnlimitedGags(not av.unlimitedGags)
    return 'Toggled unlimited gags %s for %s' % ('ON' if av.unlimitedGags else 'OFF', av.getName())

@magicWord(category=CATEGORY_STAFF)
def maxCogPage():
    """ Max the target's discovered cogs. """
    target = spellbook.getTarget()
    deptCount = len(SuitDNA.suitDepts)
    target.b_setCogCount(list(CogPageGlobals.COG_QUOTAS[1]) * deptCount)
    cogStatus = [CogPageGlobals.COG_COMPLETE2] * SuitDNA.suitsPerDept
    target.b_setCogStatus(cogStatus * deptCount)
    target.b_setCogRadar([1, 1, 1, 1])
    target.b_setBuildingRadar([1, 1, 1, 1])
    return 'Maxed %s\'s discovered cogs!' % (target.getName())

@magicWord(category=CATEGORY_LEADER)
def immortal():
    """ Make target (if 500+) or self (if 499-) immortal. """
    av = spellbook.getTarget() if spellbook.getInvokerAccess() >= 500 else spellbook.getInvoker()
    av.setImmortalMode(not av.immortalMode)
    return 'Toggled immortal mode %s for %s' % ('ON' if av.immortalMode else 'OFF', av.getName())

@magicWord(category=CATEGORY_LEADER, types=[str, int])
def summoncogdo(track="s", difficulty=5):
    tracks = CogdoUtil.getAllowedTracks()

    if track not in tracks:
        return "Invalid track!"

    av = spellbook.getInvoker()
    building = av.findClosestDoor()
    if building == None:
        return "No Toon building found!"

    building.cogdoTakeOver(difficulty, 2, track)
    return 'Successfully spawned cogdo with track %s and difficulty %d' % (track, difficulty)

@magicWord(category=CATEGORY_STAFF, types=[int, int])
def emblems(silver=10, gold=10):
    spellbook.getTarget().addEmblems((gold, silver))
    return 'Restocked with Gold: %s Silver: %d' % (gold, silver)

@magicWord(category=CATEGORY_STAFF)
def catalog():
    simbase.air.catalogManager.deliverCatalogFor(spellbook.getTarget())

@magicWord(category=CATEGORY_STAFF, types=[str])
def remCode(code):
    av = spellbook.getTarget()
    if av.isCodeRedeemed(code):
        av.removeCode(code)
        return 'Player can now reuse the code %s' % code
    else:
        return "Player hasn't redeemed this code!"

@magicWord(category=CATEGORY_STAFF, types=[int])
def shovelSkill(skill):
    """
    Update shovel skill.
    """
    av = spellbook.getTarget()
    av.b_setShovelSkill(skill)

@magicWord(category=CATEGORY_STAFF, types=[int])
def canSkill(skill):
    """
    Update watering can skill.
    """
    av = spellbook.getTarget()
    av.b_setWateringCanSkill(skill)

@magicWord(category=CATEGORY_DEVELOPER, types=[int, str])
def epp(dept, command="add"):
    av = spellbook.getTarget()
    if command == "add":
        av.addEPP(dept)

    elif command == "remove":
        av.removeEPP(dept)

    elif command == "get":
        if dept == -1:
            return av.epp

        return av.hasEPP(dept)

    else:
        return "Unknown command!"

@magicWord(category=CATEGORY_LEAD_STAFF, types=[int])
def promote(dept):
    spellbook.getTarget().b_promote(dept)

@magicWord(category=CATEGORY_STAFF)
def maxGarden():
    av = spellbook.getInvoker()
    av.b_setShovel(3)
    av.b_setWateringCan(3)
    av.b_setShovelSkill(639)
    av.b_setWateringCanSkill(999)

@magicWord(category=CATEGORY_TRIAL, types=[int], access=103)
def badge(gmId):
    if not 0 <= gmId <= 5:
        return 'Staff-Badges: 0=off, 1=Trial, 2=Staff, 3=Lead-Staff, 4=Developers, 5=Leaders'

    if (spellbook.getInvokerAccess() < 103) and (gmId > 1):
        return 'This badge is for trial-staff only!'

    elif (spellbook.getInvokerAccess() < 502) and (gmId > 2):
        return 'This badge is for staff only!'

    elif (spellbook.getInvokerAccess() < 504) and (gmId > 3):
        return 'This badge is for lead-staff only!'

    elif (spellbook.getInvokerAccess() < 508) and (gmId > 4):
        return 'This badge is for developers only!'

    elif (spellbook.getInvokerAccess() < 701) and (gmId > 5):
        return 'Your Not A Leader, Only Leaders can have this special badge!'

    if spellbook.getTarget().isGM() and gmId != 0:
        spellbook.getTarget().b_setGM(0)

    spellbook.getTarget().b_setGM(gmId)

    return 'You have set %s to badge type %s' % (spellbook.getTarget().getName(), gmId)

@magicWord(category=CATEGORY_STAFF, types=[int])
def goto(avIdShort):
    """ Teleport to the avId specified. """
    avId = 100000000+avIdShort # To get target doId.
    toon = simbase.air.doId2do.get(avId)
    if not toon:
        return "Unable to teleport to target, they are not currently on this district."
    spellbook.getInvoker().magicWordTeleportRequests.append(avId)
    toon.sendUpdate('magicTeleportRequest', [spellbook.getInvoker().getDoId()])

@magicWord(category=CATEGORY_STAFF, types=[str, int])
def exp(track, amt):
    """ Set your experience to the amount specified for a single track. """
    trackIndex = TTLocalizer.BattleGlobalTracks.index(track)
    av = spellbook.getTarget()
    av.experience.setExp(trackIndex, amt)
    av.b_setExperience(av.experience.makeNetString())
    return "Set {0} exp to {1:d} successfully.".format((track, amt))
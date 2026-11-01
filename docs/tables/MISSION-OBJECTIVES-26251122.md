# 任务目标定义表（game.dll .data 0x2CA65D0，build 26251122）

> 一句话：`Mission/end` 请求里的 `objectives[].id` **不是黑盒 hash** —— 它是 game.dll `.data` 里一张
> 152 条记录的「目标定义表」的行键；每条记录带**名称 locid、描述 locid**，以及一个**关联 badge/统计 id**。
> 本轮据此把 6 局任务的目标全部翻译成了游戏内文案（见 §3）。
>
> 交叉源：`refs/strings-en-26088801.json`（locid→文案，24,834 条）、本 build 明文 `.data`、5 局 API 抓包
> （`D:\mod\out\gwe\req_*Mission_end.json`）。方法与本仓库其它表文档一致：整列命中排除巧合。

## 1. 定位与结构（✓ 本轮解出）

| 项 | 值 |
|---|---|
| 表起点 | **`0x2CA65D0`**（`game.dll` 文件偏移）|
| 记录长度 | **`0xA0`**（152 条，`0x2CA65D0`–`0x2CAC430`）|
| `+0x00` | **目标 hash** = API `objectives[].id`（u32）|
| `+0x04` | 0（固定）|
| `+0x08` | 指向同族 locid 的引用 id（如 0x82149310；与名称/描述同区递增）⚠ 未展开 |
| `+0x0C` | 1（固定）|
| `+0x10` | 小枚举（1/2/3，疑为"目标类型/权重"）⚠ |
| `+0x34` / `+0x38` | **名称 locid（两槽同值，重复存放）** |
| `+0x3C` | **描述 locid** |
| `+0x54` | **关联 badge/统计 id**（0 = 无；非 0 时与结算 `badges[].id32` 同命名空间，见 §4）|

判据：① 5 局共 **17 个不同** `objectives[].id` 全部在表内命中（2^32 下随机命中概率 ~0）；
② 解出的名称与任务语境逐条吻合（例：100 号星球打"EXTERMINATE TERMINIDS"、防守战"EVACUATE PRIORITY CITIZENS"、
城市战"3×DESTROY AUTOMATON COMMAND BUNKER"）；③ 描述 locid 与名称 locid 属于同一批 strings。

## 2. 目标 hash 的副本

同一 hash 在文件里出现 **19 次**：一次是本节表的记录键（`0x2CAxxxx`），其余 18 次分布在
`0x1FBFE00` 起的一组 hash 数组里（每个数组长度/位置不同，和 `.text` 加密无关，都在明文 `.data`）。
这些数组只存 hash、不含名称；**名称只能从 0x2CA65D0 的表里拿**。

## 3. 全表（152 条；空名 = 该目标在 strings 里没有名字，可能是内部/废弃条目）

| # | 偏移 | hash | 名称 | 描述 | +0x54 |
|---:|---|---|---|---|---:|
| 1 | 0x2CA65D0 | 3397563563 | DESTROY EGGS | Large quantities of eggs are located in this area. Use any means necessary to de… | 0 |
| 2 | 0x2CA6670 | 294427958 | DESTROY SPORE LUNG | The Spore Lung is located deep within this Terminid tunnel complex. | 0 |
| 3 | 0x2CA6710 | 3017625790 | SHRIEKER NEST | A nest of flying Shriekers has been reported in this area. | 0 |
| 4 | 0x2CA67B0 | 605080777 | DESTROY INFESTED TOWER | This building has been overrun by Terminids and is now a Shrieker breeding groun… | 0 |
| 5 | 0x2CA6850 | 42559104 | PREVENT SPIRE GROWTH |  | 0 |
| 6 | 0x2CA68F0 | 1659905001 | SPORE SPEWER | This Terminid hive node emits a dense fog which reduces visibility. | 0 |
| 7 | 0x2CA6990 | 182683792 | DESTROY SPORE SPEWER | This Terminid hive node emits a dense fog which reduces visibility. | 0 |
| 8 | 0x2CA6A30 | 4173830979 | STALKER LAIR | A dense nest of Stalkers has been sighted in this area. | 0 |
| 9 | 0x2CA6AD0 | 199153955 | ELIMINATE BROOD COMMANDER | Surveillance suggests a Brood Commander is in this location. | 0 |
| 10 | 0x2CA6B70 | 3032143519 | ELIMINATE CHARGER | A Charger was last sighted in this region. | 0 |
| 11 | 0x2CA6C10 | 2637893484 | ELIMINATE BILE TITAN | Reports indicate that a Bile Titan was last observed in this location. | 0 |
| 12 | 0x2CA6CB0 | 127182789 | NUKE NURSERY CHAMBER | A Nursery Chamber is located here, ripe with millions of feeding larvae who tunn… | 0 |
| 13 | 0x2CA6D50 | 1510866745 | DEPLOY THUMPER | [Seismic readouts] indicate a high Terminid activity [just South of Mt. St. Melo… | 0 |
| 14 | 0x2CA6DF0 | 2537980357 | SPREAD DEMOCRACY | The Terminids have transformed this world into a bastion of Fascist oppression. … | 0 |
| 15 | 0x2CA6E90 | 839495937 | RETRIEVE MUTANT LARVA | Deep cover intelligence has, through highly classified and heroic means, identif… | 0 |
| 16 | 0x2CA6F30 | 748741543 | RECOVER SSSD | An SSSD Hard Drive containing valuable data was lost at this location following … | 0 |
| 17 | 0x2CA6FD0 | 3272793774 | RECOVER SCIENTIFIC SPECIMENS | The Terminids have stolen highly valuable specimens of enemy larvae and eggs. Re… | 0 |
| 18 | 0x2CA7070 | 2924095901 | BUG HORDE | A massive enemy army has been spotted in the area. Thin their ranks, stay your g… | 3181424819 |
| 19 | 0x2CA7110 | 2621213607 | EXTERMINATE TERMINIDS | A dense swarm of Terminids has amassed in this region. | 3071768642 |
| 20 | 0x2CA71B0 | 426586917 | EXTERMINATE TERMINIDS | A dense Terminid swarm is located here. Eradicate it. | 3071768642 |
| 21 | 0x2CA7250 | 3409436273 | SEAL BUG HOLES | A cluster of hive entrances has been mapped in this region. | 357290428 |
| 22 | 0x2CA72F0 | 333852789 | ACTIVATE TCS+ STATION | Bring each of the three battery silos online to activate this TCS+ station. | 3181424819 |
| 23 | 0x2CA7390 | 2464469546 | ACTIVATE TCS+ STATION | Bring each of the three battery silos online to activate this TCS+ station. | 3181424819 |
| 24 | 0x2CA7430 | 175894917 | DEACTIVATE TERMICIDE TOWER | Deactivate the battery silos to shut down the dispersion of Termicide. | 3181424819 |
| 25 | 0x2CA74D0 | 824768011 | ERADICATE MUTATED NESTS |  | 3181424819 |
| 26 | 0x2CA7570 | 629858657 | DEPLOY DARK FLUID | The TCS created several fissures in the planet's crust in this area. A Drill str… | 0 |
| 27 | 0x2CA7610 | 2314105256 | PAYLOAD SITE |  | 0 |
| 28 | 0x2CA76B0 | 2477589196 | ELIMINATE IMPALER | Tectonic disturbances indicate the presence of an Impaler in this area. | 0 |
| 29 | 0x2CA7750 | 3071909565 | EXTERMINATE TERMINIDS | A dense swarm of Terminids has amassed in this region. | 3071768642 |
| 30 | 0x2CA77F0 | 1483431343 | RESTORE PUMP SITE | Restart the pumps located in this region. | 0 |
| 31 | 0x2CA7890 | 2685762593 | EXTRACT E-711 | The Rapid Modular Drilling Platform is located here. | 0 |
| 32 | 0x2CA7930 | 3343406073 | RESTORE PUMP SITE | Restart the pumps located in this region. | 0 |
| 33 | 0x2CA79D0 | 4272734039 | EXTRACT ORGANIC PLASMA | Organic plasma is synthesized in these vats. Siphon it for scientific analysis. | 0 |
| 34 | 0x2CA7A70 | 314263221 | EXTRACT INTEL | The high-value intel is located here. It is locked inside a secure containment u… | 0 |
| 35 | 0x2CA7B10 | 1823227688 | STRATAGEM JAMMER | This Automaton device prevents the use of any stratagems in the area. | 0 |
| 36 | 0x2CA7BB0 | 2874082761 | DETECTOR TOWER | This tower will summon Bot Dropships if intruders are detected. | 0 |
| 37 | 0x2CA7C50 | 1847319652 | DESTROY AIR BASE CONTROL TOWER | This Control Tower is the nexus of enemy aerial operations in the region. | 0 |
| 38 | 0x2CA7CF0 | 2989988832 | DESTROY COUNTER-ORBITAL CANNON | A Counter-Orbital Cannon is positioned at this site. | 0 |
| 39 | 0x2CA7D90 | 3008251626 | ANTI-AIR EMPLACEMENT | This anti-aircraft emplacement is preventing the spread of liberty across the sk… | 0 |
| 40 | 0x2CA7E30 | 1142476438 | ANTI-AIR EMPLACEMENT | This anti-aircraft emplacement is preventing the spread of liberty across the sk… | 0 |
| 41 | 0x2CA7ED0 | 3025459658 | MORTAR EMPLACEMENT | The Automatons have a mortar emplacement in the area. They will fire on anyone t… | 0 |
| 42 | 0x2CA7F70 | 4186030791 | INTERCEPT CONVOY | A heavily reinforced Automaton convoy is expected to cross through this region. … | 0 |
| 43 | 0x2CA8010 | 1470611843 | ELIMINATE DEVASTATOR | SEAF troops report sightings of a Devastator in this area. | 0 |
| 44 | 0x2CA80B0 | 1817557506 | ELIMINATE HULK | An Automaton Hulk was last reported in this location. | 0 |
| 45 | 0x2CA8150 | 967215513 | CAPTURE AUTOMATON TERRITORY | This location has been strategically chosen to maximize the flag's inspirational… | 0 |
| 46 | 0x2CA81F0 | 1685147015 | ANNEX QUARRY | The Automatons are stealing the minerals of this planet from our citizens at thi… | 0 |
| 47 | 0x2CA8290 | 3446226037 | RETRIEVE THE CHEMICALS | [Atmospheric analyses have indicated high concentrations of cyanogen chloride], … | 0 |
| 48 | 0x2CA8330 | 4174710496 | DESTROY DROPSHIPS | Automaton Dropships are docked at this location. | 0 |
| 49 | 0x2CA83D0 | 1151263561 | DESTROY FREIGHTERS | Refinery products are shipped for further processing via freighters docked here.… | 0 |
| 50 | 0x2CA8470 | 3543392909 | DESTROY STOCKPILED AMMUNITION | Intel indicates that the Automatons are stockpiling ammunition in this location. | 0 |
| 51 | 0x2CA8510 | 2818709830 | DESTROY FUEL RESERVES | Satellite imagery confirms that the Automatons are operating a fuel depot in thi… | 0 |
| 52 | 0x2CA85B0 | 3519271818 | SEAF SAM-SITE | Abandoned SEAF Anti-Aircraft Missile Launchers will fire on enemy airborne targe… | 0 |
| 53 | 0x2CA8650 | 1603565013 | ELIMINATE ANNIHILATOR TANK | Reports indicate that the Annihilator Tank was last observed in this location. | 0 |
| 54 | 0x2CA86F0 | 2812034511 | DESTROY AUTOMATON COMMAND BUNKER | This heavily-guarded bunker is thought to contain a vital Command Node for the A… | 0 |
| 55 | 0x2CA8790 | 4288114266 | DESTROY BIO-PROCESSORS | The bio-processors here are the first step in synthesis of organic plasma. They … | 0 |
| 56 | 0x2CA8830 | 2820732955 | DESTROY BIO-PROCESSORS | The bio-processors here are the first step in synthesis of organic plasma. They … | 0 |
| 57 | 0x2CA88D0 | 3217359591 | DESTROY TRANSMISSION NETWORK | The antenna responsible for the local Automaton Transmission Stream is thought t… | 0 |
| 58 | 0x2CA8970 | 4039472260 | NEUTRALIZE ORBITAL CANNON | An Orbital Cannon is located here. Infiltrate the site and use a Hellbomb to des… | 0 |
| 59 | 0x2CA8A10 | 1965641461 | GUNSHIP FACILITY | Automaton Gunships are being manufactured in this area. | 0 |
| 60 | 0x2CA8AB0 | 2405760609 | ELIMINATE FACTORY STRIDER | Orbital infrared scans have detected a Factory Strider in this area. | 0 |
| 61 | 0x2CA8B50 | 854415039 | Automaton Horde | A massive enemy army has been spotted in the area. Thin their ranks, stay your g… | 3181424819 |
| 62 | 0x2CA8BF0 | 1403625494 | ERADICATE AUTOMATON FORCES | Heavy Automaton forces are gathered in this location. | 3071768642 |
| 63 | 0x2CA8C90 | 3839088378 | DESTROY AUTOMATON FABRICATORS | Aerial scanning has identified high levels of Automaton production in this area. | 357290428 |
| 64 | 0x2CA8D30 | 3324965008 | OBTAIN COORDINATES | Coordinates of potential ore strains, identified by the Automatons, are located … | 0 |
| 65 | 0x2CA8DD0 | 2940833323 | SEIZE HIGH-GRADE PLATINUM | A cache of 99% purity platinum is located here. The Automatons intend to use thi… | 0 |
| 66 | 0x2CA8E70 | 2620314992 | SEIZE HIGH-GRADE PLATINUM | A cache of 99% purity platinum is located here. The Automatons intend to use thi… | 0 |
| 67 | 0x2CA8F10 | 897494237 | APPROPRIATE REFINERY | Raw ore is refined into high-grade platinum at this refinery. Seize control of i… | 0 |
| 68 | 0x2CA8FB0 | 1473197696 | DESTROY THE FACTORIES | Overload the Factories' output to cause an explosion and destroy them. | 0 |
| 69 | 0x2CA9050 | 3462789081 | COLLECT MINERAL DATA | This is a potential platinum-rich site identified by the Automatons. Take a site… | 0 |
| 70 | 0x2CA90F0 | 3977876117 | RETRIEVE KEYCARD | The Automatons use a highly-advanced keycard security system. A keycard located … | 0 |
| 71 | 0x2CA9190 | 4167872764 | ANTI-AIR EMPLACEMENT | This anti-aircraft emplacement is preventing the spread of liberty across the sk… | 0 |
| 72 | 0x2CA9230 | 2486789803 | MORTAR EMPLACEMENT | The Automatons have a mortar emplacement in the area. They will fire on anyone t… | 0 |
| 73 | 0x2CA92D0 | 604311316 | DEMOLISH CYBORG ASSEMBLY UNIT | Inside this towering facility, Cyborgs are grown in pod-like artificial wombs. | 0 |
| 74 | 0x2CA9370 | 2911664521 | FLOOD HYDROGEN PIPELINE | A fuel station in this district powers the Cyborg Production Unit with highly co… | 0 |
| 75 | 0x2CA9410 | 1427192043 | DESTROY COOLING TOWER | A mechanical chiller at this location cools the hydrogen that flows into the Cyb… | 0 |
| 76 | 0x2CA94B0 | 3563006084 | RAZE STRATEGIC INFRASTRUCTURE |  | 0 |
| 77 | 0x2CA9550 | 336044317 | ERASE TERRORIST MEMORIALS | This square is lined with statues of tyrants and war criminals, hailed by the Cy… | 0 |
| 78 | 0x2CA95F0 | 2175754490 | COMPROMISE AUTOMATON DEFENSES |  | 0 |
| 79 | 0x2CA9690 | 4211289458 | （无） | The downed SEAF aircraft is located here. Its black box contains crucial intel. | 0 |
| 80 | 0x2CA9730 | 2410662327 | （无） | The downed SEAF aircraft is located here. Its black box contains crucial intel. | 0 |
| 81 | 0x2CA97D0 | 2648774571 | SECONDARY EXTRACTION ZONE |  | 0 |
| 82 | 0x2CA9870 | 3460906581 | TAKE DOWN OVERSHIP | Activate the Planetary Defense Cannon and use it to bring down the Illuminate Ov… | 0 |
| 83 | 0x2CA9910 | 3543302465 | SEAF SAM-SITE | Abandoned SEAF Anti-Aircraft Missile Launchers will fire on enemy airborne targe… | 0 |
| 84 | 0x2CA99B0 | 3510784179 | （无） |  | 0 |
| 85 | 0x2CA9A50 | 392848609 | （无） |  | 0 |
| 86 | 0x2CA9AF0 | 1762384380 | DESTROY HARVESTER | An Illuminate Harvester is located in this area. Find it and destroy it. | 0 |
| 87 | 0x2CA9B90 | 862960468 | （无） | A massive enemy army has been spotted in the area. Thin their ranks, stay your g… | 3181424819 |
| 88 | 0x2CA9C30 | 3479785117 | ERADICATE ILLUMINATE FORCES | Illuminate forces have amassed here. | 3071768642 |
| 89 | 0x2CA9CD0 | 2459190883 | DESTROY ILLUMINATE WARP SHIPS | Illuminate Warp Ships are docked here. Destroy them while they are vulnerable. | 357290428 |
| 90 | 0x2CA9D70 | 2209073012 | RAISE FLAG OF SUPER EARTH | Raising the symbol of Managed Democracy will send an undeniable message that Fre… | 0 |
| 91 | 0x2CA9E10 | 1884958769 | DESTROY MONOLITH | Strange Illuminate monoliths seem to be creating fields of negative energy. We d… | 0 |
| 92 | 0x2CA9EB0 | 1208961273 | PURGE ILLUMINATE RANKS |  | 0 |
| 93 | 0x2CA9F50 | 460772625 | DISMANTLE WARP GATEWAY | DISMANTLE WARP GATEWAY - temporary description | 0 |
| 94 | 0x2CA9FF0 | 205488198 | COGNITIVE DISRUPTOR | An arcane Illuminate device at this location is creating a mind-disruption field… | 0 |
| 95 | 0x2CAA090 | 3623634977 | （无） |  | 0 |
| 96 | 0x2CAA130 | 4242987804 | （无） |  | 0 |
| 97 | 0x2CAA1D0 | 2300258124 | DESTROY LASER OBELISK | DESTROY LASER OBELISK - temporary description | 0 |
| 98 | 0x2CAA270 | 815891913 | DISRUPT EXOSPIRE CORE | The Exospire is located here. Its power core is housed in a subterranean chamber… | 0 |
| 99 | 0x2CAA310 | 3699923192 | （无） |  | 0 |
| 100 | 0x2CAA3B0 | 113532289 | （无） |  | 0 |
| 101 | 0x2CAA450 | 2355908758 | DISRUPT SHIELD GENERATOR | An Access Node linked to the Exospire's subterranean shield generator is station… | 0 |
| 102 | 0x2CAA4F0 | 536689130 | CONDEMN ILLICIT EXPERIMENTS | Within this laboratory, vile experiments twist upstanding citizens into grotesqu… | 0 |
| 103 | 0x2CAA590 | 3482685178 | DESTROY GAZER SPIRE | A Gazer Spire surveys the surrounding area from this vantage point. | 0 |
| 104 | 0x2CAA630 | 301311218 | ERADICATE VOID BLOSSOMS |  | 0 |
| 105 | 0x2CAA6D0 | 2766032912 | EXTRACT ANOMALOUS MATERIAL | The Ground All-Terrain Extraction Rig (GATER) is located here. | 0 |
| 106 | 0x2CAA770 | 1873210069 | CLEANSE FOUL SHRINE | This altar’s wellspring is crawling with Illuminate tadpoles, poised to evolve i… | 0 |
| 107 | 0x2CAA810 | 1279012289 | DESTROY WARP GATEWAYS | DESTROY WARP GATEWAYS | 357290428 |
| 108 | 0x2CAA8B0 | 3974623054 | SECONDARY EXTRACTION ZONE |  | 0 |
| 109 | 0x2CAA950 | 2581039914 | （无） |  | 3181424819 |
| 110 | 0x2CAA9F0 | 1252605865 | （无） |  | 3181424819 |
| 111 | 0x2CAAA90 | 881624766 | MOBILE RADAR | An abandoned SEAF Mobile Radar is located here. It can provide key information o… | 0 |
| 112 | 0x2CAAB30 | 2215130481 | SECURE BLACK BOX | A downed recon plane is crashed here. Its data is stored in a black box somewher… | 0 |
| 113 | 0x2CAABD0 | 2039960108 | UPLOAD BLACK BOX DATA | Once the black box has been secured, it must be transported to this interplaneta… | 0 |
| 114 | 0x2CAAC70 | 2261774043 | SEAF ARTILLERY | Abandoned SEAF artillery can be reactivated for ground-based support. | 0 |
| 115 | 0x2CAAD10 | 1310276243 | SEIZE THE CIVILIAN SATELLITE TOWERS |  | 0 |
| 116 | 0x2CAADB0 | 3026836252 | LAUNCH ICBM | This Nuclear Missile travels over long distances at high speeds, to strike befor… | 0 |
| 117 | 0x2CAAE50 | 1204907413 | RAISE FLAG OF SUPER EARTH | This location has been strategically chosen to maximize the flag's inspirational… | 0 |
| 118 | 0x2CAAEF0 | 1276162350 | TERMINATE ILLEGAL BROADCAST | An illegal propaganda broadcast has been traced to this location. | 0 |
| 119 | 0x2CAAF90 | 4255863235 | UPLOAD ESCAPE POD DATA | A crashed escape pod in the region contains valuable data. | 0 |
| 120 | 0x2CAB030 | 791525773 | REINFORCEMENT PODS | Hellpods will be deployed to this location upon mission launch. Due to the Super… | 0 |
| 121 | 0x2CAB0D0 | 1518299344 | SECURE TACTICAL VIDEO CAMERA | A high-definition tactical video camera has been deployed to this location. It i… | 0 |
| 122 | 0x2CAB170 | 1296444067 | EXTRACT WITH FOOTAGE | Once acquired, bring the footage to this location for secure extraction. | 0 |
| 123 | 0x2CAB210 | 3294154060 | UPLOAD DATA VIA LOCAL RELAY | This SEAF communication relay can be used to send information to ships in planet… | 0 |
| 124 | 0x2CAB2B0 | 921829158 | DELIVER CARGO TO THE PICKUP POINT |  | 0 |
| 125 | 0x2CAB350 | 933791069 | RETRIEVE THE BLACK BOX |  | 0 |
| 126 | 0x2CAB3F0 | 2917045379 | COLLECT BLACK BOX | The downed SEAF aircraft is located here. Its black box contains crucial intel. | 0 |
| 127 | 0x2CAB490 | 3400668848 | DESTROY ROGUE RESEARCH STATION | This facility contains unpatriotically produced research data, and must be razed… | 0 |
| 128 | 0x2CAB530 | 1910507766 | Investigate Rogue Research Station | A Super Earth Research station has gone silent. It may have [come under the infl… | 0 |
| 129 | 0x2CAB5D0 | 880375983 | DESTROY HARD DRIVES | The hard drives at this research station have been compromised by an enemy cyber… | 0 |
| 130 | 0x2CAB670 | 43113738 | ACTIVATE OIL PUMPS | The extractors over this massive repository of crude oil have ceased functioning… | 0 |
| 131 | 0x2CAB710 | 4249900250 | REACTIVATE POWER GENERATOR | Activating this generator will supply critically-needed power to SEAF devices in… | 0 |
| 132 | 0x2CAB7B0 | 1363824115 | RESCUE SCIENCE TEAMS | Scientists vital to the continued war effort were working in this top-secret res… | 738696266 |
| 133 | 0x2CAB850 | 3143772532 | RETRIEVE LAUNCH CODES | The missile launch code disk was left at a base in this region. | 0 |
| 134 | 0x2CAB8F0 | 1803185034 | START FUEL PUMPS | This fueling station is offline. It must be reactivated to initiate fuel distrib… | 0 |
| 135 | 0x2CAB990 | 2414664933 | COLLECT ENCRYPTED HARD DRIVE | The encrypted drives were abandoned at these coordinates. | 0 |
| 136 | 0x2CABA30 | 490010582 | DOCUMENT EVIDENCE | Concrete, undeniable evidence of unspeakable Automaton atrocities are located he… | 0 |
| 137 | 0x2CABAD0 | 2058688253 | TRANSFER OIL TO SHUTTLE | This fuel facility can be used to transfer crucial reserves to hovering shuttles… | 0 |
| 138 | 0x2CABB70 | 3441788559 | CONDUCT MOBILE EXTRACTION | Once the GATER is secured, use it to extract the resources in this area. | 0 |
| 139 | 0x2CABC10 | 121974944 | SECURE GROUND ALL-TERRAIN EXTRACTION RIG | The Ground All-Terrain Extraction Rig (GATER) is located here. | 0 |
| 140 | 0x2CABCB0 | 2312389939 | ACQUIRE SOIL SCAN DATA | The Prospecting Drill in this location can extract sediment cores, analyze their… | 0 |
| 141 | 0x2CABD50 | 246435402 | DEPLOY SEISMIC PROBE | The Seismic Probe in this location can be used to confirm the likely locations o… | 0 |
| 142 | 0x2CABDF0 | 3646226901 | ESTABLISH COMMUNICATION UPLINK | This signal tower must be calibrated to establish contact with the trapped civil… | 0 |
| 143 | 0x2CABE90 | 87399846 | EVACUATE PRIORITY CITIZENS | The civilians have taken shelter within the emergency bunkers of this facility. | 0 |
| 144 | 0x2CABF30 | 4053179156 | LIDAR STATION | Reactivating these abandoned SEAF LiDAR towers will provide invaluable geographi… | 0 |
| 145 | 0x2CABFD0 | 3725943852 | COLLECT SAMPLES | Collect Samples to help Super Earth and complete this objective | 4140461052 |
| 146 | 0x2CAC070 | 3846731770 | EVACUATE HIGH-VALUE ASSETS | The cache of high-value assets is located here. Fortify your defenses, then init… | 0 |
| 147 | 0x2CAC110 | 2218628911 | REPEL INVASION FLEET | SSA Radar has identified a fleet of Illuminate invasion ships descending upon th… | 3181424819 |
| 148 | 0x2CAC1B0 | 1950999139 | （无） |  | 0 |
| 149 | 0x2CAC250 | 350407630 | EARN YOUR HELLDIVER CAPE |  | 0 |
| 150 | 0x2CAC2F0 | 3294905266 | SEAF SAM-SITE | Abandoned SEAF Anti-Aircraft Missile Launchers will fire on enemy airborne targe… | 0 |
| 151 | 0x2CAC390 | 3586904433 | RETRIEVE ACCESS CODES | Access codes for the Planetary Defense Cannon are held at this location. | 0 |
| 152 | 0x2CAC430 | 1530061110 | SEIZE FUSION BATTERIES | A cache of cutting-edge fusion batteries are located here. They are made with st… | 0 |

> 空名记录里，有些仍带描述（例如 0x2CA9690「The downed SEAF aircraft is located here. Its black box contains crucial intel.」），
> 说明"名字槽为空"是数据作者没填，不是解析错。

## 4. `+0x54`：目标 ↔ 结算徽章的连接键

| `+0x54` | 出现的记录类型（数量）| 语义推断 |
|---:|---|---|
| 0 | 大多数目标（撤离/回收/拆迁/击杀单个单位等）| 无关联徽章 |
| **3071768642** | `EXTERMINATE TERMINIDS`×3、`ERADICATE AUTOMATON FORCES`、`ERADICATE ILLUMINATE FORCES` 等 4 条 | **清剿/歼灭类目标的共用计数 id**；本 build 5 局里 4 局结算都带它（amount 恒为 8 ⚠ 未解）|
| **3181424819** | `BUG HORDE`、`Automaton Horde`、`ACTIVATE TCS+ STATION`、`ERADICATE MUTATED NESTS`、`REPEL INVASION FLEET` 等 | 虫潮/TCS/防波类 |
| **357290428** | `SEAL BUG HOLES`、`DESTROY AUTOMATON FABRICATORS`、`DESTROY ILLUMINATE WARP SHIPS`、`DESTROY WARP GATEWAYS` | 拆建筑/封洞类 |
| 738696266 | `RESCUE SCIENCE TEAMS` | 救援类 |
| 4140461052 | `COLLECT SAMPLES` | 采集类 |

验证：`3071768642` 在本 build 5 局中只出现在"清剿类目标"的三局（解放/伪造防守/城市战）和真防守的
结算里；10/29 的"EVACUATE HIGH-VALUE ASSETS"防守局没有它（该目标 `+0x54 = 0`）✓。

## 5. 本轮 6 局目标翻译（API 实证）

| 局 | objectives[].id | 解出名称 | succeeded |
|---|---|---|---|
| 11-01 解放 100（成功）| 2621213607 | EXTERMINATE TERMINIDS | true |
| 11-01 解放 100（失败）| 2621213607 | EXTERMINATE TERMINIDS | false |
| 10-29 真防守 244 | 3846731770 | EVACUATE HIGH-VALUE ASSETS | true |
| 11-01 伪造防守 156 | 1403625494 | ERADICATE AUTOMATON FORCES | true |
| 11-01 城市 207 | 2812034511 ×3 | DESTROY AUTOMATON COMMAND BUNKER | true×3 |
| 11-01 城市 207 | 2874082761 ×2 | DETECTOR TOWER | true / false |
| 11-01 城市 207 | 3025459658 | MORTAR EMPLACEMENT | false |
| 11-01 城市 207 | 1965641461 | GUNSHIP FACILITY | false |
| 11-01 城市 207 | 4255863235 | UPLOAD ESCAPE POD DATA | true |
| 11-01 真防守 207 | 87399846 | EVACUATE PRIORITY CITIZENS | true |
| 11-01 真防守 207 | 3646226901 ×2 | ESTABLISH COMMUNICATION UPLINK | true×2 |
| 11-01 真防守 207 | 1823227688 | STRATAGEM JAMMER | false |
| 11-01 真防守 207 | 1965641461 | GUNSHIP FACILITY | true |
| 11-01 真防守 207 | 2261774043 | SEAF ARTILLERY | false |
| 11-01 真防守 207 | 4053179156 | LIDAR STATION | false |
| 11-01 真防守 207 | 3400668848 | DESTROY ROGUE RESEARCH STATION | true |

要点：
- 同一局可以有**多个同 id 目标实例**（城市战 3 个指挥地堡、防守战 2 个通信中继）；
- `succeeded` 只表示该目标完成情况，**不影响 `missionSuccess`**（本局 3 个侧目标失败仍判成功，只看撤离）；
- "目标名"与"任务类型"是两回事：同为 type 3 的防守任务，一局可能是 EVACUATE HIGH-VALUE ASSETS，另一局可能是
  EVACUATE PRIORITY CITIZENS + 侧目标组合 —— 具体目标由关卡生成器按星球/地形挑。

## 6. 未解 / 边界

1. `+0x08` 引用 id 的指向（疑似 locid 的"图标/音频"组，未展开）；
2. `+0x10` 小枚举（1/2/3）语义；
3. `+0x54` 非 0 时结算里的 amount 规则（`3071768642` 恒为 8 ⚠）；
4. 记录之外是否还有第二张目标表（本表只覆盖"可挂到 Mission/end objectives[] 的目标"；地图 POI 名基本都在内，
   但像 `SCORCHED EARTH` 之类的战役级效果不在此表）。

## 7. 复现

```bash
python - <<'PY'
import json,struct
sm={int(k):v for k,v in json.load(open(r"D:\mod\refs\strings-en-26088801.json",encoding="utf-8")).items()}
data=open(r"D:\SteamLibrary\steamapps\common\Helldivers 2\data\game\game.dll","rb").read()
base=0x2CA65D0
for o in range(base, base+152*0xA0, 0xA0):
    h=struct.unpack("<I",data[o:o+4])[0]
    n=struct.unpack("<I",data[o+0x34:o+0x38])[0]
    d=struct.unpack("<I",data[o+0x3C:o+0x40])[0]
    print(hex(o), h, sm.get(n), "|", sm.get(d,"")[:60])
PY
```

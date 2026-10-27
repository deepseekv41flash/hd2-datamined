# 行星索引表（build 26088801）

> ⚠ **第一列是 `planet_data` 的行号，不是游戏索引**：这张表按名字字母序排列（GACRUX→GAR HAREN→GATRIA…），实测 `HEZE BAY` 行号 191 而游戏索引 **182**、`NEW STOCKHOLM` 行号 96 而游戏索引 **93**，偏移不是常数。
> 游戏索引（`planetStatus.index` / `planetActiveEffects.index`）只能从实机日志标定；名称与 locid 的对应仍可信（用 locid join 复核过）。
> 名称取自 `planet_data.+0x008` 的 locid（**本 build 数据里只有英文语料**），生态取自 `+0x1B8 PlanetType`，
> region 取自 `+0x060 RegionLowland`（指向 `region_settings` 段 1）。
> 39 行没有名字：都是模板行（`Inherits` 为空），`debug_name` 保留生态提示。
> 「当前 presence」列只有抓到 Status 时才有（网络层，不入库）。

共 **438** 行，其中 **399** 行有显示名。

| # | 名称 | 生态 | setup | region | 当前 presence | debug_name |
|---:|---|---|---|---|---|---|
| 0 | SUPER EARTH | superearth | homeworld_superearth | region_superearth |  | `planet_000` |
| 1 | KLEN DAHTH II | sandy | desert_sandy_klen_dahth_2 | region_sandy |  | `planet_001` |
| 2 | PATHFINDER V | moor | forest_moor_base | region_moor |  | `planet_002` |
| 3 | WIDOW'S HARBOR | sandy | desert_sandy_moon | region_sandy |  | `planet_003` |
| 4 | NEW HAVEN | primordial | forest_primordial_blue | region_primordial |  | `planet_004` |
| 5 | PILEN V | sandy | desert_sandy_spiky | region_sandy |  | `planet_005` |
| 6 | MERIDIAN IIa | arctic | arctic_glacier_base | region_arctic |  | `planet_006` |
| 7 | HYDROFALL PRIME | sandy | desert_sandy_mineral | region_sandy | illuminate_bodyhorror, illuminate_invading | `planet_007` |
| 8 | ZEA RUGOSIA | sandy | desert_sandy_spiky | region_sandy |  | `planet_008` |
| 9 | DARROWSPORT | sandy | desert_sandy_acid | region_sandy |  | `planet_009` |
| 10 | FORNSKOGUR II | swamp | forest_swamp_base | region_swamp |  | `planet_010` |
| 11 | MIDASBURG | moor | forest_moor_tundra | region_moor |  | `planet_011` |
| 12 | CERBERUS IIIc | sandy | desert_sandy_spiky | region_sandy |  | `planet_012` |
| 13 | PROSPERITY FALLS | primordial | forest_primordial_blue | region_primordial |  | `planet_013` |
| 14 | OKUL VI | arctic | arctic_glacier_base | region_arctic |  | `planet_014` |
| 15 | MARTYR'S BAY | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_015` |
| 16 | FREEDOM PEAK | moor | forest_moor_red | region_moor | completed_hope | `planet_016` |
| 17 | FORT UNION | moor | forest_moor_base | region_moor |  | `planet_017` |
| 18 | KELVINOR | arctic | arctic_glacier_base | region_arctic |  | `planet_018` |
| 19 | WRAITH | sandy | desert_sandy_acid | region_sandy |  | `planet_019` |
| 20 | IGLA | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_020` |
| 21 | NEW KIRUNA | arctic | arctic_glacier_base | region_arctic |  | `planet_021` |
| 22 | FORT JUSTICE | primordial | forest_primordial_purple | region_primordial | military_helldiver_training | `planet_022` |
| 23 | THE BUG QUARANTINE | sandy | desert_sandy_acid | region_sandy |  | `planet_023` |
| 24 | ZEGEMA PARADISE | primordial | forest_primordial_base | region_primordial |  | `planet_homeworld_illuminate` |
| 25 | PROVIDENCE | moor | forest_moor_red | region_moor |  | `planet_homeworld_superearth` |
| 26 | PRIMORDIA | primordial | forest_primordial_base | region_primordial |  | `planet_026` |
| 27 | SULFURA | primordial | forest_primordial_purple | region_primordial |  | `planet_027` |
| 28 | NUBLARIA I | swamp | forest_swamp_haunted | region_swamp |  | `planet_028` |
| 29 | KRAKATWO | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_029` |
| 30 | VOLTERRA | moor | forest_moor_base | region_moor |  | `planet_030` |
| 31 | CRUCIBLE | moor | forest_moor_tundra | region_moor |  | `planet_031` |
| 32 | VEIL | primordial | forest_primordial_dead | region_primordial | completed_yearning | `planet_032` |
| 33 | MARRE IV | moor | forest_moor_arid | region_moor |  | `planet_033` |
| 34 | FORT SANCTUARY | moor | forest_moor_red | region_moor |  | `planet_034` |
| 35 | SEYSHEL BEACH | primordial | forest_primordial_purple | region_primordial |  | `planet_035` |
| 36 | HELLMIRE | moor | hellmire | region_moor |  | `planet_036` |
| 37 | EFFLUVIA | sandy | desert_sandy_mineral | region_sandy |  | `planet_037` |
| 38 | SOLGHAST | swamp | forest_swamp_haunted | region_swamp |  | `planet_038` |
| 39 | DILUVIA | moor | forest_moor_tundra | region_moor |  | `planet_039` |
| 40 | VIRIDIA PRIME | sandy | desert_sandy_base | region_sandy |  | `planet_040` |
| 41 | OBARI | moor | forest_moor_base | region_moor |  | `planet_041` |
| 42 | MYRADESH | sandy | desert_sandy_spiky | region_sandy | completed_aspiration | `planet_042` |
| 43 | ATRAMA | swamp | forest_swamp_haunted | region_swamp |  | `planet_043` |
| 44 | EMERIA | sandy | desert_sandy_mineral | region_sandy |  | `planet_044` |
| 45 | BARABOS | swamp | forest_swamp_base | region_swamp | civilian_surveillance | `planet_045` |
| 46 | FENMIRE | moor | forest_moor_base | region_moor |  | `planet_046` |
| 47 | MASTIA | sandy | desert_sandy_base | region_sandy |  | `planet_047` |
| 48 | SHALLUS | primordial | forest_primordial_purple | region_primordial |  | `planet_048` |
| 49 | KRAKABOS | swamp | forest_swamp_base | region_swamp |  | `planet_049` |
| 50 | IRIDICA | primordial | forest_primordial_purple | region_primordial |  | `planet_050` |
| 51 | AZTERRA | sandy | desert_sandy_mineral | region_sandy | destroyed_by_black_hole | `planet_051` |
| 52 | AZUR SECUNDUS | sandy | desert_sandy_spiky | region_sandy |  | `planet_052` |
| 53 | IVIS | swamp | forest_swamp_base | region_swamp |  | `planet_053` |
| 54 | SLIF | sandy | desert_sandy_acid | region_sandy |  | `planet_054` |
| 55 | CARAMOOR | sandy | desert_sandy_base | region_sandy |  | `planet_055` |
| 56 | ARLIA | primordial | forest_primordial_blue | region_primordial |  | `planet_056` |
| 57 | KHARST | moor | forest_moor_red | region_moor |  | `planet_057` |
| 58 | EUKORIA | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_058` |
| 59 | MYRIUM | sandy | desert_sandy_mineral | region_sandy |  | `planet_059` |
| 60 | KERTH SECUNDUS | moor | forest_moor_tundra | region_moor |  | `planet_060` |
| 61 | PARSH | swamp | forest_swamp_base | region_swamp |  | `planet_061` |
| 62 | REAF | moor | forest_moor_base | region_moor |  | `planet_062` |
| 63 | IRULTA | primordial | forest_primordial_base | region_primordial |  | `planet_063` |
| 64 | EMORATH | primordial | forest_primordial_purple | region_primordial | black_hole_intensified | `planet_064` |
| 65 | ILDUNA PRIME | moor | forest_moor_tundra | region_moor |  | `planet_065` |
| 66 | MAW | moor | forest_moor_arid | region_moor |  | `planet_066` |
| 67 | MERIDIA | primordial | forest_primordial_base_bug | region_primordial |  | `planet_067` |
| 68 | BOREA | arctic | arctic_glacier_base | region_arctic |  | `planet_068` |
| 69 | CURIA | sandy | desert_sandy_moon | region_sandy |  | `planet_069` |
| 70 | TARSH | swamp | forest_swamp_haunted | region_swamp |  | `planet_070` |
| 71 | SHELT | moor | forest_moor_tundra | region_moor |  | `planet_071` |
| 72 | IMBER | moor | forest_moor_arid | region_moor |  | `planet_072` |
| 73 | BLISTICA | moor | forest_moor_arid | region_moor |  | `planet_073` |
| 74 | RATCH | swamp | forest_swamp_haunted | region_swamp |  | `planet_074` |
| 75 | JULHEIM | arctic | arctic_glacier_base | region_arctic | bugs_gloom, bugs_dragon | `planet_075` |
| 76 | VALGAARD | moor | forest_moor_red | region_moor | tcs_wall | `planet_076` |
| 77 | ARKTURUS | arctic | arctic_glacier_base | region_arctic |  | `planet_077` |
| 78 | ESKER | sandy | desert_sandy_acid | region_sandy | tcs_wall | `planet_078` |
| 79 | TERREK | sandy | desert_sandy_moon | region_sandy |  | `planet_079` |
| 80 | CIRRUS | primordial | forest_primordial_dead | region_primordial |  | `planet_080` |
| 81 | CRIMSICA | moor | forest_moor_red | region_moor |  | `planet_081` |
| 82 | HEETH | arctic | arctic_glacier_base | region_arctic |  | `planet_082` |
| 83 | VELD | primordial | forest_primordial_blue | region_primordial |  | `planet_083` |
| 84 | ALTA V | primordial | forest_primordial_base | region_primordial |  | `planet_084` |
| 85 | URSICA XI | primordial | forest_primordial_purple | region_primordial | destroyed_by_black_hole | `planet_085` |
| 86 | INARI | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_086` |
| 87 | SKAASH | sandy | desert_sandy_acid | region_sandy |  | `planet_087` |
| 88 | MORADESH | sandy | desert_sandy_base | region_sandy |  | `planet_088` |
| 89 | RASP | sandy | desert_sandy_moon | region_sandy |  | `planet_089` |
| 90 | BASHYR | swamp | forest_swamp_haunted | region_swamp |  | `planet_090` |
| 91 | REGNUS | primordial | forest_primordial_base | region_primordial |  | `planet_091` |
| 92 | MOG | arctic | arctic_glacier_base | region_arctic |  | `planet_092` |
| 93 | VALMOX | moor | forest_moor_red | region_moor |  | `planet_093` |
| 94 | IRO | swamp | forest_swamp_haunted | region_swamp |  | `planet_094` |
| 95 | GRAFMERE | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_095` |
| 96 | NEW STOCKHOLM | arctic | arctic_glacier_base | region_arctic |  | `planet_096` |
| 97 | OASIS | primordial | forest_primordial_base | region_primordial | force_evacuate | `planet_097` |
| 98 | GENESIS PRIME | primordial | forest_primordial_blue | region_primordial |  | `planet_098` |
| 99 | OUTPOST 32 | sandy | desert_sandy_base | region_sandy |  | `planet_099` |
| 100 | CALYPSO | sandy | desert_sandy_mineral | region_sandy |  | `planet_100` |
| 101 | ELYSIAN MEADOWS | moor | forest_moor_red | region_moor |  | `planet_101` |
| 102 | ALDERIDGE COVE | primordial | forest_primordial_dead | region_primordial |  | `planet_102` |
| 103 | TRANDOR | moor | forest_moor_tundra | region_moor |  | `planet_103` |
| 104 | EAST IRIDIUM TRADING BAY | swamp | forest_swamp_base | region_swamp |  | `planet_104` |
| 105 | LIBERTY RIDGE | moor | forest_moor_red | region_moor |  | `planet_105` |
| 106 | BALDRICK PRIME | primordial | forest_primordial_base | region_primordial |  | `planet_106` |
| 107 | THE WEIR | moor | forest_moor_base | region_moor |  | `planet_107` |
| 108 | KUPER | primordial | forest_primordial_blue | region_primordial |  | `planet_108` |
| 109 | OSLO STATION | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_109` |
| 110 | PÖPLI IX | moor | forest_moor_arid | region_moor |  | `planet_110` |
| 111 | GUNVALD | moor | forest_moor_red | region_moor |  | `planet_111` |
| 112 | DOLPH | sandy | desert_sandy_moon | region_sandy |  | `planet_112` |
| 113 | BEKVAM III | primordial | forest_primordial_purple | region_primordial |  | `planet_113` |
| 114 | DUMA TYR | moor | forest_moor_tundra | region_moor | bot_facility_jetbrigade | `planet_114` |
| 115 | VERNEN WELLS | sandy | desert_sandy_mineral | region_sandy | destroyed_by_death_laser | `planet_115` |
| 116 | AESIR PASS | primordial | forest_primordial_dead | region_primordial |  | `planet_116` |
| 117 | AURORA BAY | moor | forest_moor_tundra | region_moor |  | `planet_117` |
| 118 | PENTA | primordial | forest_primordial_dead | region_primordial |  | `planet_118` |
| 119 | GAELLIVARE | primordial | forest_primordial_base | region_primordial |  | `planet_119` |
| 120 | VOG-SOJOTH | arctic | arctic_glacier_base | region_arctic |  | `planet_120` |
| 121 | KIRRIK | primordial | forest_primordial_base | region_primordial |  | `planet_121` |
| 122 | MORTAX PRIME | sandy | desert_sandy_spiky | region_sandy |  | `planet_122` |
| 123 | WILFORD STATION | sandy | desert_sandy_acid | region_sandy |  | `planet_123` |
| 124 | PIONEER II | sandy | desert_sandy_mineral | region_sandy | tcs_wall | `planet_124` |
| 125 | ERSON SANDS | sandy | desert_sandy_spiky | region_sandy | research_generic | `planet_125` |
| 126 | SOCORRO III | swamp | forest_swamp_haunted | region_swamp | research_bio_research, tcs_wall | `planet_126` |
| 127 | BORE ROCK | swamp | forest_swamp_base | region_swamp | destroyed_by_black_hole | `planet_127` |
| 128 | FENRIR III | sandy | desert_sandy_moon | region_sandy | tcs_wall | `planet_128` |
| 129 | TURING | primordial | forest_primordial_purple | region_primordial |  | `planet_129` |
| 130 | ANGEL'S VENTURE | moor | forest_moor_tundra | region_moor | manufacturing_generic, tcs_wall | `planet_130` |
| 131 | DARIUS II | sandy | desert_sandy_acid | region_sandy | tcs_wall | `planet_131` |
| 132 | ACAMAR IV | moor | forest_moor_base | region_moor |  | `planet_132` |
| 133 | ACHERNAR SECUNDUS | moor | forest_moor_base | region_moor |  | `planet_133` |
| 134 | ACHIRD III | sandy | desert_sandy_mineral | region_sandy |  | `planet_134` |
| 135 | ACRAB XI | moor | forest_moor_red | region_moor |  | `planet_135` |
| 136 | ACRUX IX | arctic | arctic_glacier_coldrocky | region_arctic | dss_augmentation | `planet_136` |
| 137 | ACUBENS PRIME | primordial | forest_primordial_purple | region_primordial | illuminate_engineer | `planet_137` |
| 138 | ADHAFERA SECUNDUS | primordial | forest_primordial_purple | region_primordial |  | `planet_138` |
| 139 | ADHARA | moor | forest_moor_arid | region_moor |  | `planet_139` |
| 140 | AFOYAY BAY | moor | forest_moor_base | region_moor |  | `planet_140` |
| 141 | AIN-5 | primordial | forest_primordial_dead | region_primordial |  | `planet_141` |
| 142 | ALADFAR CXI | primordial | forest_primordial_base | region_primordial |  | `planet_142` |
| 143 | ALAIRT III | primordial | forest_primordial_blue | region_primordial |  | `planet_143` |
| 144 | ALAMAK VII | primordial | forest_primordial_purple | region_primordial |  | `planet_144` |
| 145 | ALARAPH | primordial | forest_primordial_dead | region_primordial |  | `planet_145` |
| 146 | ALATHFAR XI | arctic | arctic_glacier_base | region_arctic |  | `planet_146` |
| 147 | ANDAR | moor | forest_moor_tundra | region_moor |  | `planet_147` |
| 148 | ASPEROTH PRIME | swamp | forest_swamp_base | region_swamp |  | `planet_148` |
| 149 | BELLATRIX | moor | forest_moor_base | region_moor |  | `planet_149` |
| 150 | BOTEIN | sandy | desert_sandy_acid | region_sandy |  | `planet_150` |
| 151 | OSUPSAM | sandy | desert_sandy_base | region_sandy |  | `planet_151` |
| 152 | BRINK-2 | primordial | forest_primordial_blue | region_primordial |  | `planet_152` |
| 153 | BUNDA SECUNDUS | moor | forest_moor_tundra | region_moor |  | `planet_153` |
| 154 | CANOPUS | sandy | desert_sandy_spiky | region_sandy |  | `planet_154` |
| 155 | CAPH | swamp | forest_swamp_base | region_swamp |  | `planet_155` |
| 156 | CASTOR | sandy | desert_sandy_mineral | region_sandy |  | `planet_156` |
| 157 | DURGEN | sandy | desert_sandy_base | region_sandy |  | `planet_157` |
| 158 | DRAUPNIR | moor | forest_moor_base | region_moor | seaf | `planet_158` |
| 159 | MORT | primordial | forest_primordial_dead | region_primordial |  | `planet_159` |
| 160 | INGMAR | moor | forest_moor_red | region_moor |  | `planet_160` |
| 161 | CHARA | sandy | desert_sandy_spiky | region_sandy | manufacturing_forge | `planet_161` |
| 162 | CHARBAL-VII | sandy | desert_sandy_acid | region_sandy | bot_facility_data | `planet_162` |
| 163 | CHARON PRIME | moor | forest_moor_red | region_moor |  | `planet_163` |
| 164 | CHOEPESSA IV | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_164` |
| 165 | CHOOHE | sandy | desert_sandy_base | region_sandy |  | `planet_165` |
| 166 | CHORT BAY | sandy | desert_sandy_acid | region_sandy |  | `planet_166` |
| 167 | CLAORELL | sandy | desert_sandy_moon | region_sandy |  | `planet_167` |
| 168 | CLASA | swamp | forest_swamp_base | region_swamp | tcs_wall | `planet_168` |
| 169 | CURSA | magma | desert_magma_base | region_magma |  | `planet_169` |
| 170 | DEMIURG | moor | forest_moor_tundra | region_moor | tcs_wall, bugs_super_predator | `planet_170` |
| 171 | DENEB SECUNDUS | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_171` |
| 172 | ELECTRA BAY | moor | forest_moor_base | region_moor |  | `planet_172` |
| 173 | ENULIALE | moor | forest_moor_red | region_moor |  | `planet_173` |
| 174 | EPSILON PHOENCIS VI | arctic | arctic_glacier_base | region_arctic |  | `planet_174` |
| 175 | ERATA PRIME | sandy | desert_sandy_spiky | region_sandy | tcs_wall | `planet_175` |
| 176 | ERRANT | primordial | forest_primordial_blue | region_primordial |  | `planet_176` |
| 177 | ESTANU | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_177` |
| 178 | FORI PRIME | sandy | desert_sandy_mineral | region_sandy |  | `planet_178` |
| 179 | FURY | magma | desert_magma_base | region_magma |  | `planet_179` |
| 180 | GACRUX | swamp | forest_swamp_base | region_swamp |  | `planet_180` |
| 181 | GAR HAREN | swamp | forest_swamp_haunted | region_swamp |  | `planet_181` |
| 182 | GATRIA | moor | forest_moor_red | region_moor |  | `planet_182` |
| 183 | GEMMA | primordial | forest_primordial_blue | region_primordial |  | `planet_183` |
| 184 | GRAND ERRANT | moor | forest_moor_arid | region_moor |  | `planet_184` |
| 185 | HADAR | arctic | arctic_glacier_base | region_arctic | illuminate_bodyhorror | `planet_185` |
| 186 | HAKA | primordial | forest_primordial_dead | region_primordial |  | `planet_186` |
| 187 | HALDUS | swamp | forest_swamp_base | region_swamp |  | `planet_187` |
| 188 | HALIES PORT | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_188` |
| 189 | HERTHON SECUNDUS | moor | forest_moor_arid | region_moor |  | `planet_189` |
| 190 | HESOE PRIME | arctic | arctic_glacier_base | region_arctic |  | `planet_190` |
| 191 | HEZE BAY | sandy | desert_sandy_base | region_sandy |  | `planet_191` |
| 192 | HORT | moor | forest_moor_base | region_moor |  | `planet_192` |
| 193 | HYDROBIUS | sandy | desert_sandy_spiky | region_sandy |  | `planet_193` |
| 194 | KARLIA | moor | forest_moor_arid | region_moor |  | `planet_194` |
| 195 | KARON BAY | magma | desert_magma_base | region_magma |  | `planet_195` |
| 196 | KEID | sandy | desert_sandy_base | region_sandy |  | `planet_196` |
| 197 | KHANDARK | swamp | forest_swamp_haunted | region_swamp |  | `planet_197` |
| 198 | K | magma | desert_magma_base | region_magma |  | `planet_198` |
| 199 | KLAKA 5 | swamp | forest_swamp_haunted | region_swamp |  | `planet_199` |
| 200 | KNETH PORT | moor | forest_moor_arid | region_moor |  | `planet_200` |
| 201 | KRAZ | sandy | desert_sandy_mineral | region_sandy | bot_facility_comms | `planet_201` |
| 202 | KUMA | sandy | desert_sandy_mineral | region_sandy |  | `planet_202` |
| 203 | LASTOFE | sandy | desert_sandy_base | region_sandy | elite_bot_jumpattack | `planet_203` |
| 204 | LENG SECUNDUS | sandy | desert_sandy_acid | region_sandy |  | `planet_204` |
| 205 | LESATH | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_205` |
| 206 | MAIA | sandy | desert_sandy_moon | region_sandy |  | `planet_206` |
| 207 | MALEVELON CREEK | primordial | forest_primordial_blue | region_primordial | manufacturing_industry | `planet_207` |
| 208 | MANTES | primordial | forest_primordial_base | region_primordial |  | `planet_208` |
| 209 | MARFARK | arctic | arctic_glacier_base | region_arctic |  | `planet_209` |
| 210 | MARTALE | moor | forest_moor_tundra | region_moor |  | `planet_210` |
| 211 | MATAR BAY | moor | forest_moor_base | region_moor | tcs_wall | `planet_211` |
| 212 | MEISSA | primordial | forest_primordial_base | region_primordial | bugs_burrower, bugs_dragon, bugs_hive_lord | `planet_212` |
| 213 | MEKBUDA | sandy | desert_sandy_mineral | region_sandy |  | `planet_213` |
| 214 | MENKENT | moor | forest_moor_arid | region_moor |  | `planet_214` |
| 215 | MERAK | primordial | forest_primordial_blue | region_primordial | bugs_burrower, seaf | `planet_215` |
| 216 | MERGA IV | swamp | forest_swamp_haunted | region_swamp |  | `planet_216` |
| 217 | MINCHIR | primordial | forest_primordial_blue | region_primordial |  | `planet_217` |
| 218 | MINTORIA | moor | forest_moor_base | region_moor | tcs_wall | `planet_218` |
| 219 | MORDIA 9 | primordial | forest_primordial_purple | region_primordial |  | `planet_219` |
| 220 | MOX | magma | desert_magma_base | region_magma |  | `planet_220` |
| 221 | NABATEA SECUNDUS | swamp | forest_swamp_base | region_swamp |  | `planet_221` |
| 222 | NAVI VII | primordial | forest_primordial_base | region_primordial |  | `planet_222` |
| 223 | NIVEL 43 | primordial | forest_primordial_dead | region_primordial |  | `planet_223` |
| 224 | OROTH | magma | desert_magma_base | region_magma |  | `planet_224` |
| 225 | OSHAUNE | bug_hiveworld | hiveworld_moor_base | region_bug_hiveworld |  | `planet_225` |
| 226 | OVERGOE PRIME | moor | forest_moor_red | region_moor |  | `planet_226` |
| 227 | PANDION-XXIV | primordial | forest_primordial_dead | region_primordial |  | `planet_227` |
| 228 | PARTION | moor | forest_moor_arid | region_moor |  | `planet_228` |
| 229 | PEACOCK | primordial | forest_primordial_blue | region_primordial |  | `planet_229` |
| 230 | PHACT BAY | sandy | desert_sandy_base | region_sandy |  | `planet_230` |
| 231 | PHERKAD SECUNDUS | swamp | forest_swamp_base | region_swamp | illuminate_harvester | `planet_231` |
| 232 | POLARIS PRIME | sandy | desert_sandy_spiky | region_sandy |  | `planet_232` |
| 233 | POLLUX 31 | primordial | forest_primordial_base | region_primordial |  | `planet_233` |
| 234 | PRASA | sandy | desert_sandy_mineral | region_sandy |  | `planet_234` |
| 235 | PROPUS | sandy | desert_sandy_base | region_sandy |  | `planet_235` |
| 236 | RAS ALGETHI | moor | forest_moor_tundra | region_moor |  | `planet_236` |
| 237 | RD-4 | sandy | desert_sandy_moon | region_sandy |  | `planet_237` |
| 238 | ROGUE 5 | primordial | forest_primordial_base | region_primordial |  | `planet_238` |
| 239 | RIRGA BAY | sandy | desert_sandy_acid | region_sandy |  | `planet_239` |
| 240 | SEASSE | rift | forest_rift_active | region_rift |  | `planet_240` |
| 241 | SENGE 23 | sandy | desert_sandy_mineral | region_sandy |  | `planet_241` |
| 242 | SETIA | swamp | forest_swamp_haunted | region_swamp | bots_ivory_legion | `planet_242` |
| 243 | SHETE | sandy | desert_sandy_acid | region_sandy |  | `planet_243` |
| 244 | SIEMNOT | primordial | forest_primordial_blue | region_primordial |  | `planet_244` |
| 245 | SIRIUS | sandy | desert_sandy_moon | region_sandy | bots_ivory_legion | `planet_245` |
| 246 | SKAT BAY | primordial | forest_primordial_dead | region_primordial | bots_ivory_legion | `planet_246` |
| 247 | SPHERION | primordial | forest_primordial_base | region_primordial |  | `planet_247` |
| 248 | STOR THA PRIME | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_248` |
| 249 | STOUT | moor | forest_moor_red | region_moor |  | `planet_249` |
| 250 | TERMADON | moor | forest_moor_base | region_moor |  | `planet_250` |
| 251 | TIBIT | primordial | forest_primordial_purple | region_primordial |  | `planet_251` |
| 252 | TIEN KWAN | arctic | tien_kwan | region_arctic |  | `planet_252` |
| 253 | TROOST | primordial | forest_primordial_dead | region_primordial | bots_cyborgs | `planet_253` |
| 254 | UBANEA | moor | forest_moor_red | region_moor |  | `planet_254` |
| 255 | USTOTU | sandy | desert_sandy_spiky | region_sandy |  | `planet_255` |
| 256 | VANDALON IV | arctic | arctic_glacier_base | region_arctic |  | `planet_256` |
| 257 | VARYLIA 5 | moor | forest_moor_base | region_moor |  | `planet_257` |
| 258 | WASAT | sandy | desert_sandy_acid | region_sandy |  | `planet_258` |
| 259 | VEGA BAY | arctic | arctic_glacier_base | region_arctic | bugs_hive_lord, bugs_dragon | `planet_259` |
| 260 | WEZEN | moor | forest_moor_arid | region_moor | bots_cyborgs | `planet_260` |
| 261 | VINDEMITARIX PRIME | primordial | forest_primordial_purple | region_primordial | bots_ivory_legion | `planet_261` |
| 262 | X-45 | swamp | forest_swamp_base | region_swamp |  | `planet_262` |
| 263 | YED PRIOR | moor | forest_moor_red | region_moor |  | `planet_263` |
| 264 | ZEFIA | primordial | forest_primordial_purple | region_primordial |  | `planet_264` |
| 265 | ZOSMA | sandy | desert_sandy_moon | region_sandy |  | `planet_265` |
| 266 | ZZANIAH PRIME | sandy | desert_sandy_base | region_sandy |  | `planet_266` |
| 267 | SKITTER | swamp | forest_swamp_haunted | region_swamp |  | `planet_267` |
| 268 | EUPHORIA III | sandy | desert_sandy_moon | region_sandy | seaf | `planet_268` |
| 269 | DIASPORA X | sandy | desert_sandy_base | region_sandy | tcs_wall | `planet_269` |
| 270 | GEMSTONE BLUFFS | moor | forest_moor_base | region_moor | tcs_wall | `planet_270` |
| 271 | ZAGON PRIME | bug_hiveworld | hiveworld_sandy_base | region_bug_hiveworld |  | `planet_271` |
| 272 | OMICRON | bug_hiveworld | hiveworld_moor_tundra | region_bug_hiveworld | illuminate_harvester | `planet_272` |
| 273 | CYBERSTAN | arctic | arctic_cyberstan | region_arctic |  | `planet_273` |
| 274 | FRONTERIA | oasis | desert_oasis_base | region_oasis |  | `planet_274` |
| 275 | HETT | oasis | desert_oasis_base | region_oasis |  | `planet_275` |
| 276 | WORTHY I | coniferous | forest_coniferous_base | region_coniferous |  | `planet_276` |
| 277 | PINE TAR | coniferous | forest_coniferous_base | region_coniferous |  | `planet_277` |
| 278 | LONE | sandy | desert_sandy_spiky | region_sandy |  | `planet_278` |
| 279 | PEONY | sandy | desert_sandy_acid | region_sandy |  | `planet_279` |
| 280 | CALEFACTORIA | oasis | desert_oasis_base | region_oasis |  | `planet_280` |
| 281 | LUXURIANT | deciduous | forest_deciduous_base | region_deciduous |  | `planet_281` |
| 282 | SERENDIPITY XI | deciduous | forest_deciduous_autumn | region_deciduous |  | `planet_282` |
| 283 | BANKABILITY | primordial | forest_primordial_blue | region_primordial |  | `planet_283` |
| 284 | ARGENTIS | sandy | desert_sandy_moon | region_sandy |  | `planet_284` |
| 285 | PROBARE | primordial | forest_primordial_base | region_primordial |  | `planet_285` |
| 286 | CYGNIA III | primordial | forest_primordial_purple | region_primordial |  | `planet_286` |
| 287 | — | moor | forest_moor_red | region_moor |  | `planet_287` |
| 288 | COLUMBIDAE | moor | forest_moor_arid | region_moor |  | `planet_288` |
| 289 | PIPIONEM | moor | forest_moor_base | region_moor |  | `planet_289` |
| 290 | SUPERIORIA LV | coniferous | forest_coniferous_base | region_coniferous |  | `planet_290` |
| 291 | TANDEM | arctic | arctic_glacier_base | region_arctic |  | `planet_291` |
| 292 | RETRIBUTARY | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_292` |
| 293 | DEFENSIBLE | sandy | desert_sandy_spiky | region_sandy |  | `planet_293` |
| 294 | WATCHDOG 5 | primordial | forest_primordial_dead | region_primordial |  | `planet_294` |
| 295 | AQUILA XXXII | coniferous | forest_coniferous_base | region_coniferous |  | `planet_295` |
| 296 | ELIGIBLE | moor | forest_moor_base | region_moor |  | `planet_296` |
| 297 | PROBABILITY | primordial | forest_primordial_dead | region_primordial |  | `planet_297` |
| 298 | LINK B | moor | forest_moor_arid | region_moor |  | `planet_298` |
| 299 | HOPEFUL | deciduous | forest_deciduous_base | region_deciduous |  | `planet_299` |
| 300 | BICEP | magma | desert_magma_base | region_magma |  | `planet_300` |
| 301 | ADRENAL 8 | magma | desert_magma_base | region_magma |  | `planet_301` |
| 302 | NEW WISDOM | magma | desert_magma_base | region_magma |  | `planet_302` |
| 303 | NEW INSIGHT | magma | desert_magma_base | region_magma |  | `planet_303` |
| 304 | BIG ROCK | oasis | desert_oasis_base | region_oasis |  | `planet_304` |
| 305 | WAYWARD | magma | desert_magma_base | region_magma |  | `planet_305` |
| 306 | TERRENE | deciduous | forest_deciduous_base | region_deciduous |  | `planet_306` |
| 307 | ARABILITY | deciduous | forest_deciduous_autumn | region_deciduous |  | `planet_307` |
| 308 | FAMILY-FRIEND | coniferous | forest_coniferous_base | region_coniferous |  | `planet_308` |
| 309 | NASCENCE | coniferous | forest_coniferous_base | region_coniferous |  | `planet_309` |
| 310 | FLEDGE | deciduous | forest_deciduous_base | region_deciduous |  | `planet_310` |
| 311 | SAMMELSURIUM | primordial | forest_primordial_dead | region_primordial |  | `planet_311` |
| 312 | BALLOT | sandy | desert_sandy_mineral | region_sandy |  | `planet_312` |
| 313 | RESILIENCE | sandy | desert_sandy_base | region_sandy |  | `planet_313` |
| 314 | GILE | deciduous | forest_deciduous_autumn | region_deciduous |  | `planet_314` |
| 315 | LAMB'S PATCH | deciduous | forest_deciduous_base | region_deciduous |  | `planet_315` |
| 316 | FRAKENEERIA | primordial | forest_primordial_base | region_primordial |  | `planet_316` |
| 317 | SHIRAHAMA | sandy | desert_sandy_spiky | region_sandy |  | `planet_317` |
| 318 | ANDWELL | deciduous | forest_deciduous_base | region_deciduous |  | `planet_318` |
| 319 | LYNX LYNX | coniferous | forest_coniferous_base | region_coniferous |  | `planet_319` |
| 320 | ALMINA IV | moor | forest_moor_arid | region_moor |  | `planet_320` |
| 321 | AUSPICE | deciduous | forest_deciduous_base | region_deciduous |  | `planet_321` |
| 322 | RAYSTING | primordial | forest_primordial_blue | region_primordial |  | `planet_322` |
| 323 | NOSSER | sandy | desert_sandy_moon | region_sandy |  | `planet_323` |
| 324 | SATELLARIA | moor | forest_moor_red | region_moor |  | `planet_324` |
| 325 | DOUBLET II | primordial | forest_primordial_base | region_primordial |  | `planet_325` |
| 326 | GENERATION | arctic | arctic_glacier_base | region_arctic |  | `planet_326` |
| 327 | CIVILITY | coniferous | forest_coniferous_base | region_coniferous |  | `planet_327` |
| 328 | SCUTUM CANIS LUPUS | moor | forest_moor_base | region_moor |  | `planet_328` |
| 329 | LOGISTICAE | arctic | arctic_glacier_base | region_arctic |  | `planet_329` |
| 330 | STOLTHET | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_330` |
| 331 | AVILA | oasis | desert_oasis_base | region_oasis |  | `planet_331` |
| 332 | MANDILARIA | oasis | desert_oasis_base | region_oasis |  | `planet_332` |
| 333 | EMBOLD | moor | forest_moor_tundra | region_moor |  | `planet_333` |
| 334 | BASQUINE VIII | deciduous | forest_deciduous_autumn | region_deciduous |  | `planet_334` |
| 335 | LAMBAST | moor | forest_moor_base | region_moor |  | `planet_335` |
| 336 | THRASH IV | moor | forest_moor_red | region_moor |  | `planet_336` |
| 337 | MIQÉ | primordial | forest_primordial_dead | region_primordial |  | `planet_337` |
| 338 | TOR E | oasis | desert_oasis_base | region_oasis |  | `planet_338` |
| 339 | PHANTOM 1 | primordial | forest_primordial_purple | region_primordial |  | `planet_339` |
| 340 | SPOYLE | primordial | forest_primordial_base | region_primordial |  | `planet_340` |
| 341 | WILE | arctic | arctic_glacier_base | region_arctic |  | `planet_341` |
| 342 | BRILLIANCE | deciduous | forest_deciduous_base | region_deciduous |  | `planet_342` |
| 343 | — | moor | forest_moor_red | region_moor |  | `planet_343` |
| 344 | PIEA | moor | forest_moor_red | region_moor |  | `planet_344` |
| 345 | HUSARIA | moor | forest_moor_base | region_moor |  | `planet_345` |
| 346 | OSTEHOVEL | sandy | desert_sandy_base | region_sandy |  | `planet_346` |
| 347 | MINERVA | oasis | desert_oasis_base | region_oasis |  | `planet_347` |
| 348 | ZYGOS | oasis | desert_oasis_base | region_oasis |  | `planet_348` |
| 349 | — | sandy | desert_sandy_spiky | region_sandy |  | `planet_349` |
| 350 | PESTIS | primordial | forest_primordial_base | region_primordial |  | `planet_350` |
| 351 | AMITTERE | sandy | desert_sandy_mineral | region_sandy |  | `planet_351` |
| 352 | VINGE | sandy | desert_sandy_base | region_sandy |  | `planet_352` |
| 353 | — | moor | forest_moor_base | region_moor |  | `planet_353` |
| 354 | KORV | sandy | desert_sandy_moon | region_sandy |  | `planet_354` |
| 355 | CONLON COLONY | primordial | forest_primordial_blue | region_primordial |  | `planet_355` |
| 356 | DEECON | sandy | desert_sandy_spiky | region_sandy |  | `planet_356` |
| 357 | SVITJOD | sandy | desert_sandy_acid | region_sandy |  | `planet_357` |
| 358 | — | sandy | desert_sandy_mineral | region_sandy |  | `planet_358` |
| 359 | VACCA | sandy | desert_sandy_base | region_sandy |  | `planet_359` |
| 360 | OTUR | sandy | desert_sandy_acid | region_sandy |  | `planet_360` |
| 361 | SANGIS | deciduous | forest_deciduous_autumn | region_deciduous |  | `planet_361` |
| 362 | SIRIUS II | sandy | desert_sandy_moon | region_sandy |  | `planet_362` |
| 363 | HAMMARBY | sandy | desert_sandy_moon | region_sandy |  | `planet_363` |
| 364 | MOMO-1 | primordial | forest_primordial_base | region_primordial |  | `planet_364` |
| 365 | LINDOME | arctic | arctic_glacier_base | region_arctic |  | `planet_365` |
| 366 | BOHUS | primordial | forest_primordial_dead | region_primordial |  | `planet_366` |
| 367 | NIBIRU | moor | forest_moor_base | region_moor |  | `planet_367` |
| 368 | GUNNAR | sandy | desert_sandy_moon | region_sandy |  | `planet_368` |
| 369 | — | arctic | arctic_glacier_base | region_arctic |  | `planet_369` |
| 370 | URECTEM | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_370` |
| 371 | MÖNSTERÅS II | primordial | forest_primordial_base | region_primordial |  | `planet_371` |
| 372 | MONHEIM | deciduous | forest_deciduous_base | region_deciduous |  | `planet_372` |
| 373 | DUNOONIA | deciduous | forest_deciduous_autumn | region_deciduous |  | `planet_373` |
| 374 | PAYONG | moor | forest_moor_base | region_moor |  | `planet_374` |
| 375 | PENNYBRIDGE | coniferous | forest_coniferous_base | region_coniferous |  | `planet_375` |
| 376 | UNKNOWN SYSTEM | primordial | forest_primordial_base | region_primordial |  | `planet_376` |
| 377 | UNREGISTERED SYSTEM | primordial | forest_primordial_purple | region_primordial |  | `planet_377` |
| 378 | UNMAPPED SYSTEM | primordial | forest_primordial_dead | region_primordial |  | `planet_378` |
| 379 | RUINED SYSTEM | moor | forest_moor_tundra | region_moor |  | `planet_379` |
| 380 | ANOMALOUS SYSTEM | arctic | arctic_glacier_base | region_arctic |  | `planet_380` |
| 381 | CONCEALED SYSTEM | moor | forest_moor_arid | region_moor |  | `planet_381` |
| 382 | E-710-RICH SYSTEM | moor | forest_moor_tundra | region_moor |  | `planet_382` |
| 383 | ANNIHILATED SYSTEM | moor | forest_moor_red | region_moor |  | `planet_383` |
| 384 | VITAL SYSTEM | moor | forest_moor_base | region_moor |  | `planet_384` |
| 385 | UNINHABITABLE SYSTEM | sandy | desert_sandy_base | region_sandy |  | `planet_385` |
| 386 | UVP ALPHA | deciduous | forest_deciduous_crimson | region_deciduous |  | `planet_386` |
| 387 | UVP BETA | primordial | forest_primordial_dead | region_primordial |  | `planet_387` |
| 388 | UVP GAMMA | oasis | desert_oasis_bleak | region_oasis |  | `planet_388` |
| 389 | UVP DELTA | swamp | forest_swamp_haunted | region_swamp |  | `planet_390` |
| 390 | — | arctic | — | region_arctic |  | `planet_arctic_cyberstan` |
| 391 | — | arctic | — | region_arctic |  | `planet_arctic_glacier_base` |
| 392 | — | arctic | — | region_arctic |  | `planet_arctic_glacier_coldrocky` |
| 393 | — | bug_hiveworld | — | region_bug_hiveworld |  | `planet_bug_hiveworld` |
| 394 | — | magma | — | region_magma |  | `planet_desert_magma_base` |
| 395 | — | oasis | — | region_oasis |  | `planet_desert_oasis_base` |
| 396 | — | oasis | — | region_oasis |  | `planet_desert_oasis_bleak` |
| 397 | — | sandy | — | region_sandy |  | `planet_desert_sandy_acid` |
| 398 | — | sandy | — | region_sandy |  | `planet_desert_sandy_base` |
| 399 | — | sandy | — | region_sandy |  | `planet_desert_sandy_klen_dahth_2` |
| 400 | — | sandy | — | region_sandy |  | `planet_desert_sandy_mineral` |
| 401 | — | sandy | — | region_sandy |  | `planet_desert_sandy_moon` |
| 402 | — | sandy | — | region_sandy |  | `planet_desert_sandy_spiky` |
| 403 | — | coniferous | — | region_coniferous |  | `planet_forest_coniferous_base` |
| 404 | — | deciduous | — | region_deciduous |  | `planet_forest_deciduous_autumn` |
| 405 | — | deciduous | — | region_deciduous |  | `planet_forest_deciduous_base` |
| 406 | — | deciduous | — | region_deciduous |  | `planet_forest_deciduous_crimson` |
| 407 | — | moor | — | region_moor |  | `planet_forest_moor_arid` |
| 408 | — | moor | — | region_moor |  | `planet_forest_moor_base` |
| 409 | — | moor | — | region_moor |  | `planet_forest_moor_red` |
| 410 | — | moor | — | region_moor |  | `planet_forest_moor_tundra` |
| 411 | — | primordial | — | region_primordial |  | `planet_primordial_01` |
| 412 | MERIDIA | primordial | — | region_primordial |  | `planet_primordial_base_bug` |
| 413 | — | primordial | — | region_primordial |  | `planet_forest_primordial_blue` |
| 414 | — | primordial | — | region_primordial |  | `planet_forest_primordial_dead` |
| 415 | — | primordial | — | region_primordial |  | `planet_forest_primordial_purple` |
| 416 | — | rift | — | region_rift |  | `planet_forest_rift_active` |
| 417 | — | swamp | — | region_swamp |  | `planet_forest_swamp_base` |
| 418 | — | swamp | — | region_swamp |  | `planet_forest_swamp_haunted` |
| 419 | — | superearth | — | region_superearth |  | `planet_homeworld_superearth` |
| 420 | UNDISCLOSED LOCATION | sandy | — | region_sandy |  | `planet_tutorial` |
| 421 | UNDISCLOSED LOCATION | primordial | — | region_primordial |  | `planet_tutorial_02` |
| 422 | DEV_01 | deciduous | forest_deciduous_autumn | region_deciduous |  | `planet_dev_01` |
| 423 | DEV_02 | deciduous | forest_deciduous_base | region_deciduous |  | `planet_dev_02` |
| 424 | DEV_03 | oasis | desert_oasis_base | region_oasis |  | `planet_dev_03` |
| 425 | DEV_04 | deciduous | forest_deciduous_autumn | region_deciduous |  | `planet_dev_04` |
| 426 | DEV_05 | deciduous | forest_deciduous_base | region_deciduous |  | `planet_dev_05` |
| 427 | DEV_06 | oasis | desert_oasis_base | region_oasis |  | `planet_dev_06` |
| 428 | DEV_07 | deciduous | forest_deciduous_crimson | region_deciduous |  | `planet_dev_07` |
| 429 | DEV_08 | deciduous | forest_deciduous_base | region_deciduous |  | `planet_dev_08` |
| 430 | DEV_09 | oasis | desert_oasis_bleak | region_oasis |  | `planet_dev_09` |
| 431 | VOID SOURCE PLANET | rift | forest_rift_active | region_rift |  | `planet_dev_10` |
| 432 | — | bug_hiveworld | bug_hiveworld | region_generation_testing |  | `planet_generation_testing` |
| 433 | HELLMIRE | moor | forest_moor_arid | region_moor |  | `planet_036` |
| 434 | — | bug_hiveworld | bug_hiveworld | region_bug_hiveworld |  | `planet_bug_hiveworld` |
| 435 | — | bug_hiveworld | bug_hiveworld | region_bug_hiveworld |  | `planet_bug_hiveworld` |
| 436 | — | bug_hiveworld | bug_hiveworld | region_bug_hiveworld |  | `planet_bug_hiveworld` |
| 437 | TIEN KWAN | arctic | arctic_glacier_coldrocky | region_arctic |  | `planet_252` |

# Burooj Square — Installer Device & Wiring Guide

Source project: Burooj_Square_Villa_ORIGINAL_BACKUP_20260917_172404.knxproj

## كيف تستخدم هذا الملف
هذا الدليل يفرق بين المعلومة الموجودة فعلياً داخل مشروع ETS وبين الاستنتاج المنطقي من اسم الـGroup Address ونوع الجهاز. أي شيء مكتوب عليه Inferred أو Sequential GA mapping ليس بديلاً عن المخطط الكهربائي أو ترقيم الأسلاك في الموقع.

## ما يثبته مشروع ETS حالياً
- المشروع يحتوي على قالب فيلا واحد.
- الأجهزة المادية/الوظيفية الموجودة تشمل ريليات، تحكم ستائر، DALI، لوحات لمس، لوحات مفاتيح، حساسات حضور، واجهات IR للمكيفات، وواجهة KNX-IP.
- مشروع ETS لا يسجل لي بشكل موثوق رقم الكابل الميداني أو اسم الحمل الكهربائي النهائي لكل طرف ريليه.

## أهم الأجهزة وطريقة التوصيل الفيزيائي المتوقعة

| Device | عنوان KNX | الجهاز | يتصل عادةً بـ | ما يثبته المشروع |
|---|---:|---|---|---|
| DI-10 | — | KUPSupply 640 | تغذية KNX/لوحة التوزيع | موجود في المشروع |
| DI-11 | 1 | KIPI SC | KNX TP + Ethernet | موجود؛ لا GAs مباشرة في الـInstance |
| DI-12/13 | 2/3 | DALI BOX Interface 64 v3 | KNX TP + DALI bus | موجودان؛ ballast mapping غير مثبت في الـInstance |
| DI-14 | 4 | MAXinBOX 8 v4 | KNX TP + 8 relay outputs | Garage + On/Off 3..8 |
| DI-15 | 5 | MAXinBOX 8 v4 | KNX TP + 8 relay outputs | On/Off 9..16 |
| DI-16 | 6 | MAXinBOX 16 v4 | KNX TP + 16 relay outputs | On/Off 17..32 |
| DI-17 | 7 | MAXinBOX 16 v4 | KNX TP + 16 relay outputs | On/Off 33..48 |
| DI-18 | 8 | MAXinBOX 24 v2 | KNX TP + 24 relay outputs | On/Off 49..72 |
| DI-19/20/21 | 9/10/11 | MAXinBOX SHUTTER 8CH v3 | KNX TP + shutter motor outputs | shutter groups 1..18 |
| DI-22..30 | 12..20 | Logic controller | KNX TP; logic only | HVAC blocks are visible in GAs |
| DI-43..46 | 23..26 | IRSC | KNX + IR emitter to indoor A/C | four devices present; no linked GAs in instances |
| DI-57..62 | 27..32 | Tecla 55 X4 | KNX TP | devices present |
| DI-63/64/72/73 | 33/34/35/36 | Tecla 55 X6 | KNX TP | devices present |
| DI-65/66 | 37/38 | TMD Plus 4 | KNX TP | control panel, no load output |
| DI-70/74 | 39/40 | TMD Plus 6 | KNX TP | names include Majlis & Dining |
| DI-71 | 41 | TMD Plus 8 | KNX TP | name includes G.F Living Areas |
| DI-85..92/98 | 43..50 | Z35 v2 | KNX TP; touch panel/thermostat/sensors per configuration | several room names are explicit |
| DI-99 | 51 | Z100 | KNX + 24VDC power + Ethernet | large set of links for lighting/blinds/HVAC/Garage |
| DI-100..103 | 52..55 | EyeZen TP v2 | KNX TP at ceiling | four devices present; no linked GAs in instances |

## توزيع مخارج الريليه — استنتاج منطقي من المشروع

DI-14 / address 4 / MAXinBOX 8 v4:
1. Relay 1 → Move Garage
2. Relay 2 → Stop Garage
3. Relay 3 → On/Off 3
4. Relay 4 → On/Off 4
5. Relay 5 → On/Off 5
6. Relay 6 → On/Off 6
7. Relay 7 → On/Off 7
8. Relay 8 → On/Off 8

DI-15 / address 5: Relay 1..8 → On/Off 9..16.
DI-16 / address 6: Relay 1..16 → On/Off 17..32.
DI-17 / address 7: Relay 1..16 → On/Off 33..48.
DI-18 / address 8: Relay 1..24 → On/Off 49..72.

**تحذير تنفيذ:** هذه المطابقة من تسلسل Group Addresses وعدد المخارج. لا تعتمد عليها لترقيم الأسلاك على الأطراف قبل مقارنتها مع electrical schedule / panel termination schedule.

## الستائر
DI-19: channels 1..8 → blinds 1..8
DI-20: channels 1..8 → blinds 9..16
DI-21: channels 1..2 → blinds 17..18
القنوات 3..8 في DI-21 لا تظهر لها Group Address links في الـInstance الحالي.

## المكيفات
مشروع ETS يحتوي طبقة HVAC واضحة من مجموعات Mode / Fan / ON/Off / Set Point / Temp. / Error Code. كما يحتوي أربع وحدات IRSC عند العناوين 23–26. نوع IRSC مخصص للتحكم بوحدات A/C عبر الأشعة تحت الحمراء، لكن المشروع الحالي لا يحدد أي IRSC مرتبط بأي غرفة أو وحدة داخلية. لذلك لا أنسب مكيفاً معيناً إلى IRSC معين بدون HVAC schedule أو room schedule.

## الكراج
يوجد Move Garage وStop Garage وحقول Info/Status. الـMove مرتبط بالـMAXinBOX عند العنوان 4، وبعض Info/Status مرتبطة أيضاً بـZ100. هذا يثبت منطق الكراج في KNX، لكنه لا يحدد terminal/cable ميدانياً.

## الإنتركم / الأبواب
لم تظهر تسمية صريحة لـIntercom أو Door أو Lock أو Entry أو Access ضمن Group Address names الحالية. لذلك لا يمكن تحديد جهاز إنتركم أو قفل باب من ملف ETS وحده. جهاز Z100 لديه قدرة تكامل Video Intercom حسب صفحة Zennio، لكن هذا لا يثبت أن التكامل مفعّل في هذا المشروع.

## الحساسات
يوجد 4 أجهزة EyeZen TP v2 على العناوين 52–55. هي حساسات حركة/إضاءة سقفية حسب مواصفات Zennio، لكن الـDeviceInstance الحالي لا يربطها مباشرةً بزوج Group Address واضح لكل دائرة إنارة.

## الملفات الجاهزة
- INSTALLER_WIRING_SCHEDULE.csv — جدول device/channel/GA/domain مع مستوى الدليل.
- INSTALLER_DEVICE_OVERVIEW.csv — جميع الأجهزة وعناوينها وعدد روابط GA.
- knx-device-map/GROUP_ADDRESS_SCHEDULE.csv — جميع الـ618 GA مع الأجهزة المرتبطة.

## تدقيق الكلمات المهمة

### Lighting
- 2052 — On/Off 3
- 2053 — On/Off 3 Info
- 2054 — On/Off 4
- 2055 — On/Off 4 Info
- 2056 — On/Off 5
- 2057 — On/Off 5 Info
- 2058 — On/Off 6
- 2059 — On/Off 6 Info
- 2060 — On/Off 7
- 2061 — On/Off 7 Info
- 2062 — On/Off 8
- 2063 — On/Off 8 Info
- 2064 — On/Off 9
- 2065 — On/Off 9 Info
- 2066 — On/Off 10
- 2067 — On/Off 10 Info
- 2068 — On/Off 11
- 2069 — On/Off 11 Info
- 2070 — On/Off 12
- 2071 — On/Off 12 Info
- 2072 — On/Off 13
- 2073 — On/Off 13 Info
- 2074 — On/Off 14
- 2075 — On/Off 14 Info
- 2076 — On/Off 15
- 2077 — On/Off 15 Info
- 2078 — On/Off 16
- 2079 — On/Off 16 Info
- 2080 — On/Off 17
- 2081 — On/Off 17 Info
- 2082 — On/Off 18
- 2083 — On/Off 18 Info
- 2084 — On/Off 19
- 2085 — On/Off 19 Info
- 2086 — On/Off 20
- 2087 — On/Off 20 Info
- 2088 — On/Off 21
- 2089 — On/Off 21 Info
- 2090 — On/Off 22
- 2091 — On/Off 22 Info
- 2092 — On/Off 23
- 2093 — On/Off 23 Info
- 2094 — On/Off 24
- 2095 — On/Off 24 Info
- 2096 — On/Off 25
- 2097 — On/Off 25 Info
- 2098 — On/Off 26
- 2099 — On/Off 26 Info
- 2100 — On/Off 27
- 2101 — On/Off 27 Info
- 2102 — On/Off 28
- 2103 — On/Off 28 Info
- 2104 — On/Off 29
- 2105 — On/Off 29 Info
- 2106 — On/Off 30
- 2107 — On/Off 30 Info
- 2108 — On/Off 31
- 2109 — On/Off 31 Info
- 2110 — On/Off 32
- 2111 — On/Off 32 Info
- 2112 — On/Off 33
- 2113 — On/Off 33 Info
- 2114 — On/Off 34
- 2115 — On/Off 34 Info
- 2116 — On/Off 35
- 2117 — On/Off 35 Info
- 2118 — On/Off 36
- 2119 — On/Off 36 Info
- 2120 — On/Off 37
- 2121 — On/Off 37 Info
- 2122 — On/Off 38
- 2123 — On/Off 38 Info
- 2124 — On/Off 39
- 2125 — On/Off 39 Info
- 2126 — On/Off 40
- 2127 — On/Off 40 Info
- 2128 — On/Off 41
- 2129 — On/Off 41 Info
- 2130 — On/Off 42
- 2131 — On/Off 42 Info
- 2132 — On/Off 43
- 2133 — On/Off 43 Info
- 2134 — On/Off 44
- 2135 — On/Off 44 Info
- 2136 — On/Off 45
- 2137 — On/Off 45 Info
- 2138 — On/Off 46
- 2139 — On/Off 46 Info
- 2140 — On/Off 47
- 2141 — On/Off 47 Info
- 2142 — On/Off 48
- 2143 — On/Off 48 Info
- 2144 — On/Off 49
- 2145 — On/Off 49 Info
- 2146 — On/Off 50
- 2147 — On/Off 50 Info
- 2148 — On/Off 51
- 2149 — On/Off 51 Info
- 2150 — On/Off 52
- 2151 — On/Off 52 Info

### HVAC
- 3073 — 1 Mode
- 3074 — 1 Mode Info
- 3077 — 1 Fan
- 3078 — 1 Fan Info
- 3079 — 1 Set Point
- 3080 — 1 Set Point Info
- 3081 — 1 Temp.
- 3082 — 1 Error Code
- 3083 — 2 Mode
- 3084 — 2 Mode Info
- 3087 — 2 Fan
- 3088 — 2 Fan Info
- 3089 — 2 Set Point
- 3090 — 2 Set Point Info
- 3091 — 2 Temp.
- 3092 — 2 Error Code
- 3093 — 3 Mode
- 3094 — 3 Mode Info
- 3097 — 3 Fan
- 3098 — 3 Fan Info
- 3099 — 3 Set Point
- 3100 — 3 Set Point Info
- 3101 — 3 Temp.
- 3102 — 3 Error Code
- 3103 — 4 Mode
- 3104 — 4 Mode Info
- 3107 — 4 Fan
- 3108 — 4 Fan Info
- 3109 — 4 Set Point
- 3110 — 4 Set Point Info
- 3111 — 4 Temp.
- 3112 — 4 Error Code
- 3113 — 5 Mode
- 3114 — 5 Mode Info
- 3117 — 5 Fan
- 3118 — 5 Fan Info
- 3119 — 5 Set Point
- 3120 — 5 Set Point Info
- 3121 — 5 Temp.
- 3122 — 5 Error Code
- 3123 — 6 Mode
- 3124 — 6 Mode Info
- 3127 — 6 Fan
- 3128 — 6 Fan Info
- 3129 — 6 Set Point
- 3130 — 6 Set Point Info
- 3131 — 6 Temp.
- 3132 — 6 Error Code
- 3133 — 7 Mode
- 3134 — 7 Mode Info
- 3137 — 7 Fan
- 3138 — 7 Fan Info
- 3139 — 7 Set Point
- 3140 — 7 Set Point Info
- 3141 — 7 Temp.
- 3142 — 7 Error Code
- 3143 — 8 Mode
- 3144 — 8 Mode Info
- 3147 — 8 Fan
- 3148 — 8 Fan Info
- 3149 — 8 Set Point
- 3150 — 8 Set Point Info
- 3151 — 8 Temp.
- 3152 — 8 Error Code
- 3153 — 9 Mode
- 3154 — 9 Mode Info
- 3157 — 9 Fan
- 3158 — 9 Fan Info
- 3159 — 9 Set Point
- 3160 — 9 Set Point Info
- 3161 — 9 Temp.
- 3162 — 9 Error Code
- 3163 — 10 Mode
- 3164 — 10 Mode Info
- 3167 — 10 Fan
- 3168 — 10 Fan Info
- 3169 — 10 Set Point
- 3170 — 10 Set Point Info
- 3171 — 10 Temp.
- 3172 — 10 Error Code
- 3173 — 11 Mode
- 3174 — 11 Mode Info
- 3177 — 11 Fan
- 3178 — 11 Fan Info
- 3179 — 11 Set Point
- 3180 — 11 Set Point Info
- 3181 — 11 Temp.
- 3182 — 11 Error Code
- 3183 — 12 Mode
- 3184 — 12 Mode Info
- 3187 — 12 Fan
- 3188 — 12 Fan Info
- 3189 — 12 Set Point
- 3190 — 12 Set Point Info
- 3191 — 12 Temp.
- 3192 — 12 Error Code
- 3193 — 13 Mode
- 3194 — 13 Mode Info
- 3197 — 13 Fan
- 3198 — 13 Fan Info

### Blinds/Shutters
- 2048 — Move Garage
- 2049 — Move Garage Info
- 2050 — Stop Garage
- 2051 — Stop Garage Info
- 2817 — 1 Move
- 2818 — 1 Stop
- 2819 — 1 Status
- 2820 — 2 Move
- 2821 — 2 Stop
- 2822 — 2 Status
- 2823 — 3 Move
- 2824 — 3 Stop
- 2825 — 3 Status
- 2826 — 4 Move
- 2827 — 4 Stop
- 2828 — 4 Status
- 2829 — 5 Move
- 2830 — 5 Stop
- 2831 — 5 Status
- 2832 — 6 Move
- 2833 — 6 Stop
- 2834 — 6 Status
- 2835 — 7 Move
- 2836 — 7 Stop
- 2837 — 7 Status
- 2838 — 8 Move
- 2839 — 8 Stop
- 2840 — 8 Status
- 2841 — 9 Move
- 2842 — 9 Stop
- 2843 — 9 Status
- 2844 — 10 Move
- 2845 — 10 Stop
- 2846 — 10 Status
- 2847 — 11 Move
- 2848 — 11 Stop
- 2849 — 11 Status
- 2850 — 12 Move
- 2851 — 12 Stop
- 2852 — 12 Status
- 2853 — 13 Move
- 2854 — 13 Stop
- 2855 — 13 Status
- 2856 — 14 Move
- 2857 — 14 Stop
- 2858 — 14 Status
- 2859 — 15 Move
- 2860 — 15 Stop
- 2861 — 15 Status
- 2862 — 16 Move
- 2863 — 16 Stop
- 2864 — 16 Status
- 2865 — 17 Move
- 2866 — 17 Stop
- 2867 — 17 Status
- 2868 — 18 Move
- 2869 — 18 Stop
- 2870 — 18 Status

### Garage
- 2048 — Move Garage
- 2049 — Move Garage Info
- 2050 — Stop Garage
- 2051 — Stop Garage Info

### Intercom/Access
- لا توجد تسمية صريحة مطابقة في أسماء Group Addresses الحالية.

### Security/Alarm
- لا توجد تسمية صريحة مطابقة في أسماء Group Addresses الحالية.

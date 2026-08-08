# **Spatial Modeling of Sub-Arctic Fuel Logistics: A Multimodal Transport Graph Network and Flight Path Analysis of Alaska's Bulk Fuel Distribution**

The extreme geographical configuration of Alaska presents a singular challenge for refined petroleum distribution. Approximately 82% to 86% of the state’s populated communities are disconnected from the primary contiguous road system. To sustain human habitation, local economies, and municipal microgrids in these sub-Arctic environments, a highly specialized, multimodal fuel distribution network is required. Refined products, principally diesel for electrical power generation and space heating, gasoline for local transport, and aviation gasoline (avgas) for regional transport, are moved across vast distances via a seasonal, interconnected network of marine shipping lanes, riverine lighterage routes, and air cargo flight paths.  
This transport network is modeled as a directed, multimodal transport graph:  
$$G \= (V, E)$$  
The vertex set $V$ defines primary refineries, import gateways, regional maritime hubs, sub-regional aviation hubs, and localized spoke communities. The directed edge set $E$ maps the physical and temporal pathways that connect these nodes, constrained by seasonal ice, water depths, and runway configurations.

## **Spatial Dataset Integration for Network Graph Construction**

To reconstruct and analyze the topology of the Alaskan bulk fuel transport graph, logistics planners must integrate several administrative, regulatory, and spatial datasets. These databases define the physical capacity, environmental exposure, regulatory compliance, and economic throughput of the nodes (V) and edges (E) in the network.

| Dataset Name | Administrative Origin | Core Spatial and Operational Data Fields | Graph Network Mapping Function |
| :---- | :---- | :---- | :---- |
| **Utilities Bulk Fuel Inventory** | Dept. of Commerce, Community, & Economic Development (DCCED) / Alaska Energy Authority (AEA) | Tank capacities, photos, engineering assessments, structural drawings, and compliance records. | Defines the volumetric capacity and structural health of the spoke community nodes (V). |
| **DCRA Bulk Fuel Tool** | Division of Community and Regional Affairs (DCRA) | Owner contact details, USCG bulk fuel inspections, enforcement history, and bulk fuel loan status. | Maps regulatory compliance and financial health attributes of individual network nodes. |
| **Alaska Fuel Price Survey** | Division of Community and Regional Affairs (DCRA) | Longitudinal bi-annual retail prices of heating fuel and gasoline across 100 surveyed communities. | Provides the cost variables required to calculate economic friction along directed edges (E). |
| **Statewide Threat Assessment** | Denali Commission / USACE / University of Alaska Fairbanks (UAF) | Vulnerability indices (0 to 3\) grading community exposure to riverine erosion, flooding, and permafrost degradation. | Quantifies the environmental decay rate and structural risk of node failures within the graph. |
| **Power Cost Equalization (PCE) Database** | Alaska Energy Authority (AEA) | Annual fuel consumption, utility generation efficiency, and retail residential electricity rates. | Establishes the demand function and fuel consumption rates at each target spoke node (V). |
| **Interactive Project Database System 2.0** | Denali Commission | Award volumes, engineering scope of work, project execution schedules, and matching fund partners. | Identifies active capital improvement projects and node-reconstruction interventions. |

Through the synthesis of these databases, the transport network can be analyzed as a dynamic system. Node capacity attributes are drawn from the DCCED bulk fuel feature service, environmental degradation parameters are modeled using the Statewide Threat Assessment, and fuel demand patterns are calculated using PCE reporting statistics.

## **Primary Gateways and Regional Bulk Fuel Hubs**

The primary gateways and regional hubs of the transport graph serve as the major consolidation points for refined petroleum entering the state. Fuel is moved from these gateways via ocean-going linehaul vessels to regional fuel hubs, which feature massive storage capacities and deep-water access.

### **Import Gateways and Refining Nodes**

Refined fuel enters the Alaskan transport network through a few highly integrated gateways. The Port of Alaska in Anchorage serves as the central receiving node, handling over 40% of all petroleum products consumed statewide. In 2019, the Port of Alaska processed 17.5 million barrels of fuel, including 10.3 million barrels received dockside. Approximately 98% of these inbound marine receipts were classified as kerosene-type jet fuels, heavily driven by the refueling needs of Ted Stevens Anchorage International Airport, which processes approximately two million gallons of aviation fuel daily.  
Following the 2015 closure of the Flint Hills refinery in North Pole, which previously supplied the airport via the Alaska Railroad, the Port of Alaska's role as an import gateway expanded significantly.  
Domestic refining is concentrated at the Marathon refinery in Nikiski (Cook Inlet) and Petro Star’s refinery in Valdez, with product subsequently distributed coastwise or trucked overland to riverine shipping gateways such as Nenana.

### **Regional Maritime Hubs**

Regional hubs function as the primary intermediate staging areas between ocean-going linehaul tankers and shallow-draft river or coastal lighterage networks. Linehaul barges, carrying between 2.5 million and 3.5 million gallons of fuel, route from Cook Inlet to these coastal hubs during the brief, ice-free summer window, which spans approximately four months in Western Alaska and is even shorter in the Arctic.

| Hub Node Name | Primary Basin / Maritime District | Storage Capacity (Gallons) | Logistical Integration & Distribution Edge Connections |
| :---- | :---- | :---- | :---- |
| **Port of Alaska (Anchorage)** | Cook Inlet / Southcentral | 3,100,000 | Serves as the primary import gateway, supplying Southcentral, the Interior, and Western hubs. |
| **Valdez Terminal** | Prince William Sound / Southcentral | Regional Terminal | Connects Trans-Alaska Pipeline System crude to Petro Star refining assets; distributes coastwise. |
| **Nenana Terminal** | Tanana & Yukon River Basin | River Terminal | Receives fuel trucked from the North Pole refinery, transferring it to river barges. |
| **Bethel Hub** | Kuskokwim River Basin / Western | 1,020,000 | Primary Kuskokwim River hub; routes fuel to riverine spokes via shallow-draft tugs and barges. |
| **Kotzebue Hub** | Chukchi Sea / Arctic Coast | 1,000,000 | Arctic coastal hub; supplies Northwest Arctic Borough villages via shallow lighterage barges. |
| **Dillingham Hub** | Bristol Bay / Southwest | 850,000 | Serves Bristol Bay region; integrates with offshore commercial fishing fleet refueling networks. |
| **Nome Hub** | Norton Sound / Seward Peninsula | Regional Hub | Direct linehaul receiving point; serves Norton Sound spoke communities. |
| **St. Michael Terminal** | Yukon River Mouth / Western | 100,000 | Sub-regional hub near the Yukon mouth; coordinates transfer of coastal barge fuel to riverine vessels. |

## **Aviation Transport Paths and Scheduled Air Cargo Networks**

When sub-Arctic winter freeze-up halts marine navigation, the directed edges of the transport graph shift from water and land routes to aviation paths. Air cargo represents the only year-round method to transport fuel and goods to off-road communities, operating on a strict "Hub and Spoke" model. Mainline air carriers fly large, scheduled cargo aircraft from major hubs (Anchorage and Fairbanks) to regional hubs, where shipments are transitioned to smaller turboprop or piston-driven aircraft for delivery to local spoke communities.  
      \[Anchorage Gateway (ANC)\]                \[Fairbanks Gateway (FAI)\]  
             │              │                               │  
             │ (Lynden)     │ (Everts)                      │ (Everts)  
             ▼              ▼                               ▼  
          \[Aniak Hub\]                     \[Kotzebue Hub\]  
          │                 │                               │  
          ├─► Alakanuk      ├─► Chuathbaluk                 ├─► Ambler  
          ├─► Kotlik        ├─► Crooked Creek               ├─► Buckland  
          └─► Mountain Vill.└─► Sleetmute                   ├─► Deering  
                                                            └─► Kiana

### **Scheduled Major Air Cargo Operations from Anchorage (ANC)**

Everts Air Cargo and Lynden Air Cargo operate scheduled Part 121 air freighter routes out of Ted Stevens Anchorage International Airport to the primary regional aviation nodes in Western and Northern Alaska.

| Destination | Flight Number | Carrier | Aircraft Type | Departure Time | Frequency | Return Window |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **Aniak (ANI)** | N/A | Everts | DC-6 / MD-80 | 3:30 pm 11:30 am | Wednesday Saturday | Returns 6:30 pm Returns 2:30 pm |
| **Bethel (BET)** | N/A | Everts | DC-6 / MD-80 | 5:30 am 7:30 am 3:00 pm | Mon \- Fri Saturday Tue, Thu | Returns 8:30 am Returns 10:30 am Returns 6:00 pm |
| **Bethel (BET)** | Flight 120 | Lynden | L-382 Hercules | 3:45 am | Tue \- Sat | Arrives 5:15 am; returns as Flight 121 at 6:15 am |
| **Dillingham (DLG)** | N/A | Everts | DC-6 / MD-80 | 11:30 am | Mon, Wed, Fri | Returns 2:30 pm |
| **Emmonak (EMK)** | Flight 130 | Lynden | L-382 Hercules | 12:00 pm | Mon, Fri | Arrives 2:00 pm; returns as Flight 131 at 3:00 pm |
| **Galena (GAL)** | N/A | Everts | DC-6 / MD-80 | 11:00 am 8:00 am | Tuesday Thursday | Returns 2:00 pm Returns 11:00 am |
| **King Salmon (AKN)** | N/A | Everts | DC-6 / MD-80 | 11:30 am | Wed, Fri | Returns 2:30 pm |
| **Kotzebue (OTZ)** | N/A | Everts | DC-6 / MD-80 | 9:00 am 1:00 pm | Tue, Thu Saturday | Returns 1:00 pm Returns 5:30 pm |
| **Kotzebue (OTZ)** | Flight 160 | Lynden | L-382 Hercules | 6:00 am | Mon, Wed, Fri | Arrives 8:00 am; returns as Flight 161 at 9:00 am |
| **Nome (OME)** | N/A | Everts | DC-6 / MD-80 | 9:00 am | Mon, Wed, Fri | Returns 1:00 pm |
| **Nome (OME)** | Flight 150 | Lynden | L-382 Hercules | 4:00 am | Tue, Thu, Sat | Arrives 6:00 am; returns as Flight 151 at 7:00 am |
| **St. Mary's (KSM)** | Flight 140 | Lynden | L-382 Hercules | 10:00 am | Tue, Thu, Sat | Arrives 11:45 am; returns as Flight 141 at 1:00 pm |
| **Unalakleet (UNK)** | N/A | Everts | DC-6 / MD-80 | 11:30 am 3:00 pm | Tuesday Friday | Returns 2:30 pm Returns 6:00 pm |

### **Scheduled Major Air Cargo Operations from Fairbanks (FAI)**

Fairbanks functions as the secondary dispatch hub, bridging fuel and freight flows to the Interior and North Slope communities.

| Destination | Departure Time | Transport Mode / Carrier | Frequency | Operational Path & Routing Specifications |
| :---- | :---- | :---- | :---- | :---- |
| **Anchorage (ANC)** | 4:00 pm | Highway Trucking | Mon \- Fri | Operates as a land edge, arriving in Anchorage at 10:00 am the next day. |
| **Kotzebue (OTZ)** | 4:00 pm | Everts Air Cargo | Mon \- Fri | Cargo consolidates in Fairbanks and routes via scheduled Anchorage flights. |
| **Aniak (ANI)** | 4:00 pm | Everts Air Cargo | Mon \- Fri | Connects via FAI-ANC trucking to Anchorage scheduled air departures. |
| **Bethel (BET)** | 4:00 pm | Everts Air Cargo | Mon \- Fri | Integrates with scheduled Anchorage flight departures. |
| **Dillingham (DLG)** | 4:00 pm | Everts Air Cargo | Mon \- Fri | Connects via scheduled Anchorage routing. |
| **King Salmon (AKN)** | 4:00 pm | Everts Air Cargo | Mon \- Fri | Integrates with scheduled Anchorage departure windows. |
| **Nome (OME)** | 4:00 pm | Everts Air Cargo | Mon \- Fri | Consolidates and transfers via the Anchorage cargo hub. |
| **Unalakleet (UNK)** | 4:00 pm | Everts Air Cargo | Mon \- Fri | Connects via scheduled Anchorage departures. |

## **Flight Path Mapping for Graph Network Analysis**

To construct an explicit directed-graph network representing fuel flight paths in Alaska, the directed edges ($E$) are mapped using scheduled air cargo routes and regional feeder services. The following table provides a structural "TO" and "FROM" mapping of primary aviation trunks and secondary hub-to-spoke distribution corridors, allowing for spatial network visualization, geographic mapping, and adjacency matrix generation:

| Origin Node (From) | Origin Code | Destination Node (To) | Destination Code | Primary Carrier | Service Type | Sources & Notes |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Anchorage | ANC | Aniak | ANI | Everts Air Cargo | Scheduled Cargo Trunk | Piston/Turboprop fleet |
| Anchorage | ANC | Bethel | BET | Everts / Lynden Air Cargo | Scheduled Cargo Trunk | Major Western hub |
| Anchorage | ANC | Dillingham | DLG | Everts Air Cargo | Scheduled Cargo Trunk | Bristol Bay hub |
| Anchorage | ANC | Emmonak | EMK | Lynden Air Cargo | Scheduled Cargo Trunk | Yukon River mouth hub |
| Anchorage | ANC | Galena | GAL | Everts Air Cargo | Scheduled Cargo Trunk | Yukon River Interior hub |
| Anchorage | ANC | King Salmon | AKN | Everts Air Cargo | Scheduled Cargo Trunk | Alaska Peninsula hub |
| Anchorage | ANC | Kotzebue | OTZ | Everts / Lynden Air Cargo | Scheduled Cargo Trunk | Northwest Arctic hub |
| Anchorage | ANC | Nome | OME | Everts / Lynden Air Cargo | Scheduled Cargo Trunk | Seward Peninsula hub |
| Anchorage | ANC | St. Mary's | KSM | Lynden Air Cargo | Scheduled Cargo Trunk | Lower Yukon hub |
| Anchorage | ANC | Unalakleet | UNK | Everts Air Cargo | Scheduled Cargo Trunk | Norton Sound hub |
| Fairbanks | FAI | Allakaket | AET | Everts Air | Scheduled Feeder | Passenger/Cargo Combi |
| Fairbanks | FAI | Anaktuvuk Pass | AKP | Everts / Wright Air Service | Scheduled Feeder | Brooks Range pass |
| Fairbanks | FAI | Arctic Village | ARC | Everts Air | Scheduled Feeder | Northeast Interior spoke |
| Fairbanks | FAI | Barter Island/Kaktovik | BTI | Everts Air | Scheduled Feeder | Beaufort Sea coast spoke |
| Fairbanks | FAI | Eagle | EAA | Everts Air | Scheduled Feeder | Upper Yukon spoke |
| Fairbanks | FAI | Fort Yukon | FYU | Everts Air | Scheduled Feeder | Yukon Flats regional hub |
| Fairbanks | FAI | Galena | GAL | Everts Air | Scheduled Feeder | Mid-Yukon connection |
| Fairbanks | FAI | Huslia | HSL | Everts Air | Scheduled Feeder | Koyukuk River spoke |
| Fairbanks | FAI | Nulato | NUL | Everts Air | Scheduled Feeder | Koyukuk region spoke |
| Fairbanks | FAI | Ruby | RBY | Everts Air | Scheduled Feeder | Yukon River spoke |
| Aniak | ANI | Chuathbaluk | CHC | Ryan Air | Hub-to-Spoke Feed | Middle Kuskokwim spoke |
| Aniak | ANI | Crooked Creek | CKD | Ryan Air | Hub-to-Spoke Feed | Middle Kuskokwim spoke |
| Aniak | ANI | Kalskag | KLG | Ryan Air | Hub-to-Spoke Feed | Lower Kuskokwim spoke |
| Aniak | ANI | Red Devil | RDV | Ryan Air | Hub-to-Spoke Feed | Middle Kuskokwim spoke |
| Aniak | ANI | Sleetmute | SLQ | Ryan Air | Hub-to-Spoke Feed | Upper Kuskokwim spoke |
| Aniak | ANI | Grayling | KGX | Ryan Air | Hub-to-Spoke Feed | Yukon-Koyukuk spoke |
| Bethel | BET | Akiachak | AKI | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Bethel | BET | Akiak | AKK | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Bethel | BET | Atmautluak | ATT | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Bethel | BET | Chefornak | CYF | Ryan Air | Hub-to-Spoke Feed | Coastal Delta spoke |
| Bethel | BET | Chevak | VAK | Ryan Air | Hub-to-Spoke Feed | Coastal Delta spoke |
| Bethel | BET | Eek | EEK | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Bay spoke |
| Bethel | BET | Goodnews Bay | GNU | Ryan Air | Hub-to-Spoke Feed | Southwest coast spoke |
| Bethel | BET | Hooper Bay | HPB | Ryan Air | Hub-to-Spoke Feed | Coastal Delta spoke |
| Bethel | BET | Kasigluk | KUK | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Bethel | BET | Kipnuk | KPN | Ryan Air | Hub-to-Spoke Feed | Coastal Delta spoke |
| Bethel | BET | Kongiganak | KKH | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Bethel | BET | Kwethluk | KWT | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Bethel | BET | Kwigillingok | KWK | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Bethel | BET | Mekoryuk | MYU | Ryan Air | Hub-to-Spoke Feed | Nunivak Island spoke |
| Bethel | BET | Napakiak | WNP | Ryan Air | Hub-to-Spoke Feed | Kuskokwim River spoke |
| Bethel | BET | Napaskiak | PKA | Ryan Air | Hub-to-Spoke Feed | Kuskokwim River spoke |
| Bethel | BET | Newtok | WWT | Ryan Air | Hub-to-Spoke Feed | Ninglick River spoke |
| Bethel | BET | Nightmute | NME | Ryan Air | Hub-to-Spoke Feed | Nelson Island spoke |
| Bethel | BET | Nunapitchuk | NUP | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Bethel | BET | Platinum | PTU | Ryan Air | Hub-to-Spoke Feed | Goodnews Bay spoke |
| Bethel | BET | Quinhagak | KWN | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Bay spoke |
| Bethel | BET | Scammon Bay | SCM | Ryan Air | Hub-to-Spoke Feed | Coastal Delta spoke |
| Bethel | BET | Toksook Bay | OOK | Ryan Air | Hub-to-Spoke Feed | Nelson Island spoke |
| Bethel | BET | Tuluksak | TLT | Ryan Air | Hub-to-Spoke Feed | Kuskokwim River spoke |
| Bethel | BET | Tuntatuliak | TUT | Ryan Air | Hub-to-Spoke Feed | Kuskokwim Delta spoke |
| Emmonak | EMK | Alakanuk | AUK | Ryan Air | Hub-to-Spoke Feed | Yukon River delta spoke |
| Emmonak | EMK | Kotlik | KOT | Ryan Air | Hub-to-Spoke Feed | Coastal Yukon spoke |
| Emmonak | EMK | Nunam Iqua | NME | Ryan Air | Hub-to-Spoke Feed | Yukon River mouth spoke |
| Kotzebue | OTZ | Ambler | ABL | Bering Air | Scheduled Hub-to-Spoke | Kobuk River valley |
| Kotzebue | OTZ | Buckland | BKC | Bering Air | Scheduled Hub-to-Spoke | Seward Peninsula |
| Kotzebue | OTZ | Deering | DRG | Bering Air | Scheduled Hub-to-Spoke | Kotzebue Sound spoke |
| Kotzebue | OTZ | Kiana | IAN | Bering Air | Scheduled Hub-to-Spoke | Kobuk River valley |
| Kotzebue | OTZ | Kivalina | KVL | Bering Air | Scheduled Hub-to-Spoke | Chukchi Sea coast |
| Kotzebue | OTZ | Kobuk | OBU | Bering Air | Scheduled Hub-to-Spoke | Kobuk River headwaters |
| Kotzebue | OTZ | Noatak | WTK | Bering Air | Scheduled Hub-to-Spoke | Noatak River valley |
| Kotzebue | OTZ | Noorvik | ORV | Bering Air | Scheduled Hub-to-Spoke | Kobuk River delta |
| Kotzebue | OTZ | Point Hope | PHO | Bering Air | Scheduled Hub-to-Spoke | Arctic coastal spoke |
| Kotzebue | OTZ | Selawik | WLK | Bering Air | Scheduled Hub-to-Spoke | Inland lake spoke |
| Kotzebue | OTZ | Shungnak | SHG | Bering Air | Scheduled Hub-to-Spoke | Kobuk River valley |
| Nome | OME | Brevig Mission | KTS | Bering Air | Scheduled Hub-to-Spoke | Port Clarence spoke |
| Nome | OME | Elim | ELI | Bering Air | Scheduled Hub-to-Spoke | Norton Sound spoke |
| Nome | OME | Gambell | GAM | Bering Air | Scheduled Hub-to-Spoke | St. Lawrence Island |
| Nome | OME | Golovin | GLV | Bering Air | Scheduled Hub-to-Spoke | Norton Sound spoke |
| Nome | OME | Koyuk | KKA | Bering Air | Scheduled Hub-to-Spoke | Norton Sound spoke |
| Nome | OME | Savoonga | SVA | Bering Air | Scheduled Hub-to-Spoke | St. Lawrence Island |
| Nome | OME | Shishmaref | SHH | Bering Air | Scheduled Hub-to-Spoke | Chukchi Sea barrier |
| Nome | OME | Teller | TLA | Bering Air | Scheduled Hub-to-Spoke | Port Clarence spoke |
| Nome | OME | Wales | WAA | Bering Air | Scheduled Hub-to-Spoke | Bering Strait spoke |
| Nome | OME | White Mountain | WMO | Bering Air | Scheduled Hub-to-Spoke | Fish River valley spoke |
| Unalakleet | UNK | Shaktoolik | SKK | Bering Air | Scheduled Hub-to-Spoke | Norton Sound spoke |
| Unalakleet | UNK | St. Michael | SMK | Bering Air | Scheduled Hub-to-Spoke | Southern Norton Sound |
| Unalakleet | UNK | Stebbins | WBB | Bering Air | Scheduled Hub-to-Spoke | Southern Norton Sound |

## **Technical Parameters of the Specialty Fuel-Hauling Fleet**

To service unpaved, short, and soft gravel runways in rural Alaska, cargo carriers must operate highly specialized aircraft. Standard commercial air freighters are unsuited for these runways, making rugged, vintage airframes and custom turboprops essential for bulk fuel delivery.

| Aircraft Model | Max Fuel Payload (Gallons) | Max Payload (Lbs) | Propulsion System | Minimum Runway (Ft) | Core Operational Function & Runway Integration |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Lockheed L-382 Hercules** | 6,000 | 48,000 | 4 x Turboprops | 3,000 | Uses flat-lay cargo deck bladders; operates on short, unpaved gravel strips. |
| **Douglas DC-6** | 5,000 | 28,000 | 4 x P\&W R-2800 Radials | 3,500 | Configured with internal fuselage fuel tanks for direct bulk fuel hauling. |
| **Curtiss-Wright C-46** | 2,000 | 15,000 | 2 x Radial Engines | 3,500 | Twin-engine historic utility freighter used for lower-volume spoke deliveries. |
| **Air Tractor AT-802** | 800 | 8,800 | 1 x Pratt & Whitney PT6A | \< 2,000 | Crop-duster design; uses a modified hopper to transport fuel to restricted runways. |

The operational physics of operating vintage piston-driven aircraft like the DC-6 are highly complex. Everts Air Cargo estimates a ratio of 12 maintenance hours for every single flying hour to keep the DC-6 fleet operational. Finding aviation gasoline (avgas) and sourcing spare parts for these 60-year-old Pratt & Whitney radial engines present ongoing logistical challenges.  
The safety risks of bulk fuel air transport are highlighted by several operational incidents :

* In March 1992, Everts Air Fuel DC-6BF (N151) overran the 960-meter ice-covered runway at Selawik Airport when its reverse thrust failed.  
* In December 2000, Everts Curtiss C-46 (N1419Z), returning from Nondalton after delivering 7,800 liters of fuel, suffered a controlled flight into terrain (CFIT) near Kenai, resulting in two fatalities.  
* In January 2001, Everts DC-6B (N4390F), carrying 18,500 liters of fuel oil, suffered a wing separation and crashed during a winter landing at the Donlin Creek Airstrip.

These aviation pathways are supported by specialized ground equipment. In winter, when aircraft payload limits restrict flights, multi-modal carriers use PistenBully snowcats to drag heavy freight sleighs over snowpack and ice roads, and hovercrafts with a 12,500-pound cargo capacity to traverse frozen rivers and marshes.

## **Piston-Engine Aviation Dependence and the Unleaded Fuel Transition Bottleneck**

A major systemic vulnerability within the Alaskan transport network is its deep operational dependency on piston-engine aircraft. These aircraft rely on leaded 100 octane low lead (100LL) aviation gasoline. While the Federal Aviation Administration (FAA) and environmental agencies have initiated a transition to unleaded avgas under the Eliminate Aviation Gasoline Lead Emissions (EAGLE) initiative, the logistics of this transition are uniquely difficult in Alaska.

### **Structural Dependence on Leaded Avgas**

Piston-engine aircraft are critical commercial infrastructure in rural Alaska. Data from the Bureau of Transportation Statistics (BTS) T-100 database outlines the scale of this dependency :

* Over 50% of active commercial air carriers operating intra-Alaska routes maintain at least one piston-engine aircraft in their active fleet.  
* Commercial piston aircraft recorded 130,850 flights within Alaska, transporting 201,729 passengers and 30.6 million pounds of cargo annually.  
* For non-hub, remote "bush" spoke communities, piston-engine aircraft perform nearly 50% of all commercial flights, delivering 30% of all passengers and 20% of all recorded air cargo.

These piston flights deliver daily necessities, emergency medical supplies, and mail to communities in the Southeast, Southwest, and Kodiak regions.

### **The Logistics Transition Bottleneck**

The scheduled transition away from leaded 100LL to unleaded alternatives (such as G100UL) by the extended deadline of December 31, 2032, creates several logistical challenges :  
$$\\text{Transition Vulnerability} \= f\\left(\\frac{1}{\\text{Barge Window}}, \\text{Storage Cells}, \\text{Linehaul Unit Cost}\\right)$$  
This vulnerability is shaped by three key factors:

1. **Seasonal Barge Windows:** Fuel delivery to remote communities relies on marine and river barges that operate during brief summer windows. Coordinating the replacement of fuel inventories and swapping out storage tanks must be completed during this restricted timeframe.  
2. **Bulk Importation Constraints:** Refined fuels are imported into Alaska in shipments of at least 2 million gallons to maintain economic viability. Separating supply lines to import leaded and unleaded avgas simultaneously during the transition period could reduce shipment volumes and increase unit costs.  
3. **Lack of Storage Redundancy:** Most rural village tank farms are designed to store fuel from "barge to barge," utilizing single-tank designs with no separate cells to hold distinct fuel lines. The lack of storage tank redundancy at spoke nodes makes it physically impossible to store both leaded 100LL and new unleaded avgas at the same time during the multi-year transition.

## **Graph Systemic Vulnerability and Infrastructure Maintenance Backlog**

The bulk fuel infrastructure of rural Alaska is in an advanced state of decay, presenting environmental, safety, and economic risks. The physical assets that make up the nodes (V) of the transport graph are highly vulnerable to localized climate impacts and geotechnical failures.

### **Geotechnical Node Degradation**

Of the more than 400 bulk fuel facilities in rural Alaska, the average facility age is over 40 years, with many exceeding 50 years. These facilities are undergoing structural degradation driven by sub-Arctic environmental processes :

* **Permafrost Thawing and Frost Jacking:** Thawing permafrost causes soil subsidence, making fuel tanks lean and structural piping shear.  
* **Riverine and Coastal Erosion:** Rapid shoreline erosion actively threatens barge and airport fuel headers, rendering incoming directed edges (E) unusable.  
* **Toppling and Structural Failure:** During extreme weather events, such as Typhoon Merbok, unanchored tank systems have been toppled by rising floodwaters, causing catastrophic spills.

Upgrading a single village bulk fuel facility to code-compliant standards costs between $4 million and $10 million and takes 2 to 5 years to complete. The total deferred maintenance backlog across the state's rural bulk fuel infrastructure is projected to approach $1.5 billion.

### **Capital Upgrades and Prioritization Metrics**

To prioritize funding, the Alaska Energy Authority (AEA) evaluates several key metrics, including:

* The proximity of facilities to eroding shorelines or flood zones.  
* Compliance with USCG, EPA, and ADEC spill containment regulations.  
* The structural condition of foundations, airport/barge headers, and secondary containment structures.  
* Facility size, prioritizing larger regional hubs over smaller spoke nodes to maximize efficiency.

In July 2025, the Denali Commission, in partnership with the EPA and the Alaska Native Tribal Health Consortium (ANTHC), awarded a landmark $100 million grant to upgrade tank farms in ten highly vulnerable communities. This three-year initiative (August 1, 2025 – July 30, 2028\) addresses critical nodes facing severe environmental risks :

| Prioritized Spoke Node | Graph Node Type | Primary Geotechnical / Climate Threat | Logistical Connectivity and Access |
| :---- | :---- | :---- | :---- |
| **Aniak** | Sub-Regional Hub | Riverbank erosion threatening airfield and local tank farms. | River barge and scheduled Everts DC-6 air access. |
| **Shageluk** | Spoke Node | Riverine flooding; foundation damage from ice-run impacts. | Seasonal river barge access; high delivery costs. |
| **Eek** | Spoke Node | Coastal flooding; permafrost collapse and soil shifting. | Highly shallow, restricted lighterage barge access. |
| **Kivalina** | Spoke Node | Extreme coastal erosion; storm surge flooding. | Beach landing only; highly restricted summer window. |
| **Kobuk** | Spoke Node | River migration; shallow water constraints limiting barge access. | Extremely shallow river drafts; seasonal barge access. |
| **Noatak** | Spoke Node | Riverbank erosion threatening fuel delivery line headers. | Restricted shallow river barge access. |
| **Tuluksak** | Spoke Node | Permafrost degradation causing structural tank tilt. | River barge access via the Kuskokwim River. |
| **Wales** | Spoke Node | Coastal storms and shore erosion. | Unimproved beach landing; highly seasonal. |
| **Russian Mission** | Spoke Node | Soil instability and river erosion. | River barge access along the Yukon River. |
| **Quinhagak** | Spoke Node | Permafrost thaw and coastal flood exposure. | Coastal lighterage barge access. |

## **Analytical Conclusions and Strategic Network Recommendations**

To address the systemic vulnerabilities of Alaska’s fuel distribution network, several logistical and infrastructure interventions should be prioritized :

### **Marine and River Channel Maintenance**

The physical depth constraints of Western Alaska's rivers limit the carrying capacity of lighterage barges, requiring multiple half-load trips that increase distribution costs. Targeted river dredging and the construction of simple, reinforced beach tie-up points would allow barges to transport higher fuel volumes per trip, reducing transit times and reliance on favorable tides.

### **Consolidation of Spoke Tank Farms**

Many rural communities maintain multiple small, separate bulk fuel tanks owned by different local entities, such as the city, the tribe, and the local school district. Consolidating these fragmented facilities into a single, modern, code-compliant community tank farm served by a single beach header would eliminate the need for multiple deliveries within the same village, reducing offloading risks and lowering fuel costs.

### **Siting Sub-Regional Fuel Depots**

Establishing strategically positioned, high-capacity bulk fuel depots—such as the proposed facility at Williamsport—would allow distributors to stage fuel closer to remote markets. These depots would minimize the travel distance of shallow-draft river barges, creating crucial buffer stock to protect against short river-navigation seasons and unexpected droughts.

### **Intertie Development**

Constructing high-voltage transmission interties between neighboring villages would allow communities with modern, efficient generators to share power with adjacent spokes. This intertie network would reduce the need for bulk diesel storage at every spoke node, lowering the volume of fuel that must be transported and stored in environmentally sensitive areas.  

/* Tahoe Transit Study site configuration.
   Every link, file path, embed ID, and meeting date the page uses lives here.
   Edit this file to swap a link or add a meeting. The page itself holds only copy.
   Every image and file is in this repo or on trpa.gov. Nothing loads from the old Squarespace site. */

window.SITE_CONFIG = {
  contact: {
    name: "Kira Richardson",
    title: "Senior Transportation Planner",
    email: "krichardson@trpa.gov"
  },

  survey: {
    title: "Tahoe Transit Study Survey",
    itemId: "d49378edcde44d33ad51f498b09e4c4c",
    shortUrl: "https://arcg.is/0Kv8eu0"
    // share URL and iframe URL are built from itemId in the page
  },

  // Home page report links (hosted on trpa.gov)
  reports: [
    { title: "Transit Study Executive Summary", href: "https://www.trpa.gov/wp-content/uploads/Tahoe-Transit-Study-Draft-Executive-Summary.pdf" },
    { title: "Draft Transit Study", href: "https://www.trpa.gov/wp-content/uploads/TahoeTransitStudy-Draft102826.pdf" },
    { title: "Existing Conditions Report", href: "https://www.trpa.gov/wp-content/uploads/TRPAExistingConditionsMemo-Final22526.pdf" },
    { title: "Existing Conditions Report: Appendices A to C", href: "https://www.trpa.gov/wp-content/uploads/AppendicesA-C.pdf" }
  ],

  // Funding tab: detailed funding tables behind the chart
  fundingTables: [
    { title: "Federal funds", href: "https://www.trpa.gov/wp-content/uploads/FederalFunds-10.28.2026.pdf" },
    { title: "State funds", href: "https://www.trpa.gov/wp-content/uploads/StateFunds-10.28.2026.pdf" },
    { title: "Local funds, part 1 of 3", href: "https://www.trpa.gov/wp-content/uploads/LocalFunds1of3-7columns-10.28.2026.pdf", accent: "#F6633B" },
    { title: "Local funds, part 2 of 3", href: "https://www.trpa.gov/wp-content/uploads/LocalFunds2of3-7columns-10.28.2026.pdf", accent: "#F6633B" },
    { title: "Local funds, part 3 of 3", href: "https://www.trpa.gov/wp-content/uploads/LocalFunds3of3-6columns-10.28.2026.pdf", accent: "#F6633B" }
  ],

  // Flourish visualizations (public)
  flourish: {
    funding: "27797632"   // transit operations funding (Sankey), Existing conditions tab
  },

  // Images. Paths are in this repo.
  images: {
    hero:       { src: "./assets/img/hero-tart-bus-boarding.jpg", credit: "Photo: Generikal" },
    involved:   { src: "./assets/img/survey-ttd-bus-stop.jpg", credit: "Photo: Drone Promotions, courtesy of TTD" },
    governance: { src: "./assets/img/governance-chart.jpg" }
  },

  // Project Partners tab. logo is a path in this repo. href is optional.
  partners: {
    team: [
      { name: "Tahoe Regional Planning Agency", logo: "./assets/img/trpa-logo-color.png", href: "https://www.trpa.gov/" },
      { name: "LSC Transportation Consultants", logo: "./assets/img/partners/lsc.png" },
      { name: "TY Lin", logo: "./assets/img/partners/tylin.png", href: "https://www.tylin.com/" }
    ],
    stakeholders: [
      { name: "Tahoe Regional Planning Agency (TRPA)", logo: "./assets/img/trpa-logo-color.png", href: "https://www.trpa.gov/" },
      { name: "City of South Lake Tahoe", logo: "./assets/img/partners/cslt.png", href: "https://www.cityofslt.gov/" },
      { name: "Tahoe Truckee Area Regional Transit (TART)", logo: "./assets/img/partners/tart.png", href: "https://tahoetruckeetransit.com/" },
      { name: "Douglas County", logo: "./assets/img/partners/douglas-county.png", href: "https://www.douglascountynv.gov/" },
      { name: "Tahoe Transportation District (TTD)", logo: "./assets/img/partners/ttd.png", href: "https://www.tahoetransportation.org/" },
      { name: "El Dorado County", logo: "./assets/img/partners/el-dorado-county.png", href: "https://www.eldoradocounty.ca.gov/Home" },
      { name: "Truckee/North Tahoe Transportation Management Association (TNTTMA)", logo: "./assets/img/partners/tnt-tma.png", href: "https://tnttma.com/" },
      { name: "Placer County", logo: "./assets/img/partners/placer-county.png", href: "https://www.placer.ca.gov/" },
      { name: "Carson Area Metropolitan Planning Organization (CAMPO)", logo: "./assets/img/partners/campo.png", href: "https://www.carsoncity.gov/government/departments-g-z/public-works/transportation/campo-carson-area-metropolitan-planning-organization" },
      { name: "RTC Washoe", logo: "./assets/img/partners/washoe-rtc.png", href: "https://rtcwashoe.com/" },
      { name: "Washoe County", logo: "./assets/img/partners/washoe-county.png", href: "https://www.washoecounty.gov/" },
      { name: "South Shore Transportation Management Association (SSTMA)", logo: "./assets/img/partners/sstma.png", href: "https://ss-tma.org/" }
    ]
  },

  // Draft recommendations tab: responsibility matrix data (in this repo) and the AG Grid library
  recommendationsData: "data/recommendations-matrix.js",
  agGrid: "https://cdn.jsdelivr.net/npm/ag-grid-community@33.3.2/dist/ag-grid-community.min.js",

  // Meetings. The page sorts these into Upcoming and Past by today's date.
  // date is YYYY-MM-DD. link is optional.
  meetings: [
    { date: "2027-01-21", body: "Douglas County Board of County Commissioners", time: "10 a.m.", place: "1616 Eighth Street, Minden, NV 89423", link: { label: "Meeting materials and online meeting link", href: "https://www.douglascountynv.gov/GOVERNMENT/board-of-county-commissioners/bocc-agenda-and-minutes" } },
    { date: "2027-01-07", body: "Truckee North Tahoe Transportation Management Association", time: "8 a.m.", place: "Town of Truckee Building, Prosser Room, 10183 Truckee Airport Rd., Truckee, CA 96161", link: { label: "Meeting materials and online meeting link", href: "https://tnttma.com/tma-board-agenda/" } },
    { date: "2026-12-18", body: "South Shore Transportation Management Association", time: "8:30 a.m.", place: "Lisa Maloff University Center, Lake Tahoe Community College, 1 College Drive, South Lake Tahoe, CA 96150", link: { label: "Meeting materials and online meeting link", href: "https://ss-tma.org/board-meetings/" } },
    { date: "2026-12-02", body: "Tahoe Transportation District Board", time: "3 p.m.", place: "128 Market Street, Stateline, NV 89449", link: { label: "Meeting materials and online meeting link", href: "https://tahoetransportation.org/meetings-and-agendas/?1583860264=171" } },
    { date: "2026-11-18", body: "TRPA Transportation Committee", time: "9 a.m.", place: "128 Market Street, Stateline, NV 89449", link: { label: "Meeting materials and online meeting link", href: "https://www.trpa.gov/meeting-materials/" } },
    { date: "2026-10-29", body: "South Tahoe Transit Joint Powers Authority", time: "9:30 a.m.", place: "1901 Lisa Maloff Way, South Lake Tahoe, CA 96150", link: { label: "Agenda", href: "https://slt.granicus.com/AgendaViewer.php?view_id=6&event_id=1530" } },
    { date: "2026-08-21", body: "South Shore Transportation Management Association", time: "8:30 a.m.", place: "Lisa Maloff University Center, Lake Tahoe Community College, 1 College Drive, South Lake Tahoe, CA 96150", link: { label: "Agenda", href: "https://ss-tma.org/board-meetings/" } },
    { date: "2026-08-05", body: "Tahoe Transportation District Board", time: "3 p.m.", place: "128 Market Street, Stateline, NV 89449", link: { label: "Agenda", href: "https://tahoetransportation.org/wp-content/uploads/2026/07/2026-8-5-TTD-C-Board-Agenda-Packet.pdf" } },
    { date: "2026-07-30", body: "South Tahoe Transit Joint Powers Authority", time: "9:30 a.m.", place: "1901 Lisa Maloff Way, South Lake Tahoe, CA 96150", link: { label: "Agenda", href: "https://d3n9y02raazwpg.cloudfront.net/slt/fc9df76e-844e-11f1-bb61-005056a89546-805e687c-9266-48f6-8c9d-aa26b5b78d20-1785170768.pdf" } },
    { date: "2026-04-30", body: "South Tahoe Transit Joint Powers Authority", time: "9:30 a.m.", place: "1901 Lisa Maloff Way, South Lake Tahoe, CA 96150", link: { label: "Agenda", href: "https://d3n9y02raazwpg.cloudfront.net/slt/581007c6-295e-11f1-bb28-005056a89546-5c7c4fe4-84cb-4317-b8ef-0c329738dcd2-1777054770.pdf" } },
    { date: "2026-03-04", body: "Tahoe Transportation District Board", time: "3 p.m.", place: "128 Market Street, Stateline, NV 89449", link: { label: "Agenda", href: "https://www.tahoetransportation.org/wp-content/uploads/2026/02/2026-3-4-TTD-Meeting-Agenda-Packet.pdf" } },
    { date: "2026-02-25", body: "TRPA Transportation Committee", time: "8:30 a.m.", place: "128 Market Street, Stateline, NV 89449", link: { label: "Board packet", href: "https://www.trpa.gov/wp-content/uploads/February-25-2026-Governing-Board-Packet.pdf" } },
    { date: "2026-02-05", body: "Douglas County Board of County Commissioners", time: "10 a.m.", place: "1616 Eighth Street, Minden, NV 89423", link: { label: "Agenda", href: "https://granicus_production_attachments.s3.amazonaws.com/douglascountynv/282b0fb8ee8e466d4cf766412b11bc330.pdf" } }
  ]
};

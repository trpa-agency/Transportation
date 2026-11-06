/* Tahoe Transit Study site configuration.
   Every link, file path, embed ID, and meeting date the page uses lives here.
   Edit this file to swap a link or add a meeting. The page itself holds only copy.

   Files still hosted on the old Squarespace site are marked SQUARESPACE.
   Replace those URLs before the Squarespace site is shut off. */

window.SITE_CONFIG = {
  squarespace: "https://tahoetransitstudy.squarespace.com",  // SQUARESPACE base for /s/ file links
  imageBase: "https://images.squarespace-cdn.com/content/v1/694198d352bdfd71e737b141/",  // SQUARESPACE

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

  // Home page report links (hosted on trpa.gov). Paths starting with /s/ resolve against `squarespace`.
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
    { title: "Local funds, part 1 of 3", href: "https://www.trpa.gov/wp-content/uploads/LocalFunds1of3-7columns-10.28.2026.pdf" },
    { title: "Local funds, part 2 of 3", href: "https://www.trpa.gov/wp-content/uploads/LocalFunds2of3-7columns-10.28.2026.pdf" },
    { title: "Local funds, part 3 of 3", href: "https://www.trpa.gov/wp-content/uploads/LocalFunds3of3-6columns-10.28.2026.pdf" }
  ],

  // Flourish visualizations (public)
  flourish: {
    funding: "27797632",          // transit operations funding (Sankey), Funding tab
    historicTimeline: "28013213"  // historic timeline, Governance tab
  },

  // Images. Paths are relative to imageBase unless they start with http or ./
  images: {
    hero:       { src: "./assets/img/hero-ttd-bus-ltcc.jpg", credit: "Photo: TRPA" },
    involved:   { src: "./assets/img/survey-ttd-bus-stop.jpg", credit: "" },
    governance: { src: "./assets/img/governance-chart.jpg" }
  },

  // Email updates. The page shows a sign-up link and the privacy line.
  updates: {
    label: "Email us to get project updates",
    href: "mailto:krichardson@trpa.gov?subject=Tahoe%20Transit%20Study%20updates"
  },

  // Project Partners tab. logo paths are relative to imageBase (SQUARESPACE). href is optional.
  partners: {
    team: [
      { name: "Tahoe Regional Planning Agency", logo: "./assets/img/trpa-logo-color.png", href: "https://www.trpa.gov/" },
      { name: "LSC Transportation Consultants", logo: "a965d0ce-a5bd-44ff-a31f-df224f5b0f19/lsc-triangle-logo2%2Bno%2Btext.gif" },
      { name: "TY Lin", logo: "01b105e2-c8aa-47ae-b619-d070f1ca957e/TYLin_Logo_Black.png", href: "https://www.tylin.com/" }
    ],
    stakeholders: [
      { name: "Tahoe Regional Planning Agency (TRPA)", logo: "./assets/img/trpa-logo-color.png", href: "https://www.trpa.gov/" },
      { name: "City of South Lake Tahoe", logo: "d90bc80c-24c2-40cb-8ab2-4853a874d2fa/City+of+south+lake+tahoe.png", href: "https://www.cityofslt.gov/" },
      { name: "Tahoe Truckee Area Regional Transit (TART)", logo: "6a277b19-9748-4744-bcac-dd38442a304c/TART_Logo_Square.png", href: "https://tahoetruckeetransit.com/" },
      { name: "Douglas County", logo: "ac3ea4db-a947-4721-b121-1bd0fca54f69/Douglas+County+Logo.png", href: "https://www.douglascountynv.gov/" },
      { name: "Tahoe Transportation District (TTD)", logo: "a9029d24-f928-40b2-a9f2-100d993268ed/TTD.png", href: "https://www.tahoetransportation.org/" },
      { name: "El Dorado County", logo: "21ccc1e9-16d4-4613-b75f-c42e4b450fc1/Seal_of_El_Dorado_County_CA.png", href: "https://www.eldoradocounty.ca.gov/Home" },
      { name: "Truckee/North Tahoe Transportation Management Association (TNTTMA)", logo: "956f9554-fb8e-4cbe-a220-bcbe66594cd6/TMA_2025_Logog_Color_Blk_5415_Outlined-resize_whtbk.png", href: "https://tnttma.com/" },
      { name: "Placer County", logo: "282f6de0-0697-40ef-8513-13d1e6fb03b5/Placer+County+Logo.jpg", href: "https://www.placer.ca.gov/" },
      { name: "Town of Truckee", logo: "e6758626-3e4f-4d1b-a90d-c0b799b216ce/Town+of+Truckee.png", href: "https://www.townoftruckee.gov/" },
      { name: "RTC Washoe", logo: "9102ba36-99fb-41cf-be59-6d9602ab5543/logo-rtc.webp", href: "https://rtcwashoe.com/" },
      { name: "Washoe County", logo: "1d824962-15b6-4e06-9a47-223733ef59cb/wc_logo_stoked_blue-3.png", href: "https://www.washoecounty.gov/" },
      { name: "South Shore Transportation Management Association (SSTMA)", logo: "d74733fb-13d0-4c9e-9f60-3c573f75d0b8/sstma-logo.png", href: "https://ss-tma.org/" }
    ]
  },

  // Draft recommendations tab: responsibility matrix data (in this repo) and the AG Grid library
  recommendationsData: "data/recommendations-matrix.js",
  agGrid: "https://cdn.jsdelivr.net/npm/ag-grid-community@33.3.2/dist/ag-grid-community.min.js",

  // Meetings. The page sorts these into Upcoming and Past by today's date.
  // date is YYYY-MM-DD. link is optional.
  meetings: [
    { date: "2027-01-07", body: "Truckee North Tahoe Transportation Management Association", time: "8 a.m.", place: "Town of Truckee Building, Prosser Room, 10183 Truckee Airport Rd., Truckee, CA 96161" },
    { date: "2026-12-18", body: "South Shore Transportation Management Association", time: "8:30 a.m.", place: "Lisa Maloff University Center, Lake Tahoe Community College, 1 College Drive, South Lake Tahoe, CA 96150" },
    { date: "2026-12-02", body: "Tahoe Transportation District Board", time: "Time to be determined", place: "128 Market Street, Stateline, NV 89449" },
    { date: "2026-11-18", body: "TRPA Transportation Committee", time: "Time to be determined", place: "128 Market Street, Stateline, NV 89449" },
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

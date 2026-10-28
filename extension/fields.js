// Shared by the options page and the fill script. Safe to inject more than once.
(function () {
  if (window.RM_FIELDS) return;
  const DECLINE = "I don't wish to answer";

  // What you fill in on the settings page. [key, label, default, group, hint]
  const PROFILE = [
    ['first_name', 'First name', '', 'You'],
    ['last_name', 'Last name', '', 'You'],
    ['preferred_name', 'Preferred name', '', 'You', 'Leave blank to use your first name'],
    ['pronouns', 'Pronouns', '', 'You'],
    ['email', 'Email', '', 'You'],
    ['phone', 'Phone', '', 'You', 'Digits only works best, e.g. 5195551234'],
    ['phone_country', 'Phone country code', '+1', 'You'],
    ['phone_type', 'Phone type', 'Mobile', 'You'],
    ['address', 'Street address', '', 'Address'],
    ['city', 'City', '', 'Address'],
    ['province_state', 'Province or state', '', 'Address', 'Full name works best on dropdowns, e.g. Ontario'],
    ['postal', 'Postal or ZIP code', '', 'Address'],
    ['country', 'Country', 'Canada', 'Address'],
    ['linkedin', 'LinkedIn URL', '', 'Links'],
    ['github', 'GitHub URL', '', 'Links'],
    ['website', 'Website or portfolio', '', 'Links'],
    ['school', 'School', '', 'School'],
    ['degree', 'Degree', "Bachelor's", 'School', "e.g. Bachelor's, Bachelor of Applied Science"],
    ['major', 'Major / program', '', 'School'],
    ['gpa', 'GPA', '', 'School', 'Leave blank to skip GPA questions'],
    ['grad_month', 'Graduation month', 'May', 'School'],
    ['grad_year', 'Graduation year', '2028', 'School'],
    ['start_available', 'Earliest start date', '', 'School', 'e.g. May 2027'],
    ['work_auth_us', 'Allowed to work in the US?', 'No', 'Work eligibility'],
    ['need_sponsor_us', 'Need visa sponsorship for the US?', 'Yes', 'Work eligibility'],
    ['work_auth_ca', 'Allowed to work in Canada?', 'Yes', 'Work eligibility'],
    ['need_sponsor_ca', 'Need sponsorship for Canada?', 'No', 'Work eligibility'],
    ['citizenship_us', 'US citizen or permanent resident?', 'No', 'Work eligibility'],
    ['citizenship_ca', 'Canadian citizen or permanent resident?', 'Yes', 'Work eligibility'],
    ['relocate', 'Willing to relocate?', 'Yes', 'Work eligibility'],
    ['over_18', 'At least 18?', 'Yes', 'Work eligibility'],
    ['how_heard', 'How did you hear about us', 'LinkedIn', 'Common questions'],
    ['previously_worked', 'Worked at this company before?', 'No', 'Common questions'],
    ['ai_experience', 'Experience with AI / ML?', 'Yes', 'Common questions'],
    ['coop_enrolled', 'Enrolled in a co-op program?', 'Yes', 'Common questions'],
    ['eight_month', 'Open to an 8-month co-op?', 'Yes', 'Common questions', 'Waterloo offers 8-month streams; set No to only take 4-month terms'],
    ['us_served', 'US military service (you or spouse)?', 'No', 'Work eligibility'],
    ['clearance', 'US security clearance', "I do not have an active US government security clearance | No", 'Work eligibility', 'Also answers a yes/no "do you hold a clearance?" with No'],
    ['willing_clearance', 'Willing to obtain US clearance?', 'No', 'Work eligibility'],
    ['gender', 'Gender', 'Male', 'Voluntary (EEO)', 'These are optional on every form. Leave as "' + DECLINE + '" to skip.'],
    ['hispanic', 'Hispanic or Latino', 'No', 'Voluntary (EEO)'],
    ['race', 'Race / ethnicity', 'Chinese | Asian', 'Voluntary (EEO)', 'Most specific first, separated by "|", e.g. Chinese | Asian. It tries each until a form option matches.'],
    ['veteran', 'Veteran status', DECLINE, 'Voluntary (EEO)'],
    ['disability', 'Disability status', DECLINE, 'Voluntary (EEO)'],
  ];

  // Order matters: first match wins. Tested against the field's label text, lowercased.
  const RULES = [
    ['email', /e-?mail/],
    ['phone_country', /country (phone )?code|phone.*country|dialing code|phone code/],
    ['phone_type', /phone (type|device)|device type|type of phone/],
    ['phone_ext', /extension/],
    ['phone', /phone|mobile|cell/],
    ['preferred_name', /preferred|nick ?name/],
    ['first_name', /first.?name|given.?name|forename/],
    ['last_name', /last.?name|family.?name|surname/],
    ['middle_name', /middle/],
    ['full_name', /^(your |full |legal )?name\b|full.?name/],
    ['linkedin', /linkedin/],
    ['github', /github/],
    ['website', /website|portfolio|personal (site|url|page)|blog/],
    ['address', /address( line)? ?1|street|^address$|mailing address|^address\b/],
    ['address2', /address( line)? ?2|apt|suite/],
    ['postal', /postal|zip/],
    ['city', /\bcity\b|\btown\b/],
    ['province_state', /province|\bstate\b|region/],
    ['country', /\bcountry\b|location.*country/],
    ['ai_experience', /experience.{0,30}(artificial intelligence|machine learning|\bai\b|\bml\b)|familiar.{0,30}(artificial intelligence|\bai\b)/],
    ['willing_clearance', /willing to (obtain|get|pursue).{0,30}clearance|able to obtain.{0,30}clearance/],
    ['clearance', /security clearance|government clearance|active .{0,20}clearance|\bclearance\b/],
    ['us_served', /\bserved\b|service member|national guard|\breserves\b|military service/],
    ['coop_enrolled', /enrolled in (a )?co-?op|currently.{0,20}co-?op program|part of (a )?co-?op/],
    ['eight_month', /8[-\s]?month|eight[-\s]?month|(longer|extended) (internship|co-?op)/],
    ['school', /school|university|college|institution/],
    ['degree', /\bdegree\b|level of education|education level/],
    ['major', /major|field of study|discipline|program of study|area of study|concentration/],
    ['gpa', /\bgpa\b|grade point|cumulative average/],
    ['grad', /graduat/],
    ['start_available', /available to start|available start|earliest (possible )?start|when can you start|\bavailability\b|start date(?! month| year)/],
    ['sponsor', /sponsor/],
    ['citizenship_us', /u\.?s\.?\s*citizen|united states citizen|citizen of the u|permanent resident of the u|\bgreen card\b/],
    ['citizenship_ca', /canadian citizen|citizen of canada|canadian permanent resident|citizen or permanent resident of canada/],
    ['work_auth', /authori[sz]ed|legally (eligible|able|permitted|entitled)|eligible to work|right to work|work permit|work visa/],
    ['relocate', /relocat/],
    ['over_18', /18 years|age of 18|at least 18|over 18/],
    ['how_heard', /how did you (hear|find|learn|come)|where did you (hear|find)|^source$|how .*learn about/],
    ['previously_worked', /previously (been )?(employed|worked)|former(ly)? (employee|employed)|worked (for|at|with) .{0,40}(before|previously|in the past)|current or former/],
    ['pronouns', /pronoun/],
    ['hispanic', /hispanic|latin[oax]/],
    ['gender', /gender|\bsex\b/],
    ['race', /\brace\b|ethnic/],
    ['veteran', /veteran|military|armed forces/],
    ['disability', /disabilit/],
  ];

  const DEFAULTS = Object.fromEntries(PROFILE.map(p => [p[0], p[2]]));

  // Built-in fallback answers for recurring free-text questions. Answers you set on the
  // options page (and remembered answers) always win over these.
  const ANSWERS = [
    { q: '/c\\+\\+|c or c\\b|c\\/c\\+\\+|c programming/i', a: "At BusPlanner I built production features in C++ and C# on an ASP.NET and SQL stack, and on the Midnight Sun solar car team I write and debug embedded C on real hardware with GDB. I'm comfortable designing in both, from memory and concurrency up to clean object oriented structure." },
  ];

  // Your real roles, newest first — used to fill repeatable Work Experience blocks.
  const WORK_HISTORY = [
    { company: 'BusPlanner', title: 'Software Engineer', location: 'Waterloo, ON', start_month: 'May', start_year: '2026', end_month: 'August', end_year: '2026', current: false, description: 'Shipped production C#/ASP.NET/SQL features used by 100+ school districts, cut key page-load times ~55%, and rebuilt the team CI/CD on GitHub Actions.' },
    { company: 'University of Waterloo Computer Science Club', title: 'Software Engineer', location: 'Waterloo, ON', start_month: 'October', start_year: '2025', end_month: '', end_year: '', current: true, description: 'Built an LLM-powered event-processing pipeline, cut React rendering overhead ~40%, and raised platform uptime to ~99.9% for 3,000+ students.' },
    { company: 'Midnight Sun Solar Car Team', title: 'Software Developer', location: 'Waterloo, ON', start_month: 'August', start_year: '2025', end_month: '', end_year: '', current: true, description: 'Took firmware test coverage from 0% to ~70% across ~12 modules and sped up debugging ~4x with simulated hardware interfaces and GDB.' },
  ];
  // Education — used to fill repeatable Education blocks. Falls back to your profile fields.
  const EDUCATION = [
    { school: 'University of Waterloo', degree: "Bachelor's", field: 'Computer Science', gpa: '', start_year: '2024', end_year: '2028' },
  ];

  window.RM_FIELDS = { PROFILE, RULES, DEFAULTS, ANSWERS, WORK_HISTORY, EDUCATION, DECLINE };
})();

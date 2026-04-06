I am preparing a new release. First, generate a new entry to CHANGELOG using tools/scripts/generate_changelog.py. Second, using the new CHANGELOG entry write the release notes to RELEASE_NOTES.md using ai_system/4_orchestration/workflows/release_notes_generation/Release_Notes.tmpl and the previous release notes record as example. The Release notes should be product specific - less technical details, more motivation and product consequences. Pay special attention to architectural decisions, they are the heart of the ecosystem. Make the list of the new proposed ADRs so the readers easily see the RFCs they can analyze and comment. Third, update README.md file to reflect the actual repo information and What's new section based on the changelog and release notes you have updated. Keep only three last updates including the current one. Fourth, write a telegram post on the new update, see misc/pr/tg_channel_ai_learning.



1) Analyze diff1. 2) Write the release notes to RELEASE_NOTES.md using ai_system/4_orchestration/workflows/release_notes_generation/Release_Notes.tmpl. Create a name for this release based on main changes, see previous releases examples in RELEASE_NOTES.md. 3) Update README.md: a) What's new section, b) optionally, other parts, if needed. 4) Write a telegram post about a new release to misc/pr/tg_channel_ai_learning/, use other tg posts as an example for style and formatting.

/add diff1 misc/pr/tg_channel_ai_learning/ RELEASE_NOTES.md README.md ai_system/4_orchestration/workflows/release_notes_generation/Release_Notes.tmpl


/run release_notes_data.sh $(git describe --tags --abbrev=0) HEAD > diff1

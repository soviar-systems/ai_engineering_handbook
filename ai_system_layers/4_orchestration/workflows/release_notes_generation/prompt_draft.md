Let's prepare a new release. 
0. Remove all ephemeral files that are processed and unnecessary anymore. Make sure the files are really extracted and there is no need in them anymore before removal
1. generate a new entry to CHANGELOG using tools/scripts/generate_changelog.py. 
2. analyze the changelog and extract 3-4 main topics that have been during the release development. write the release notes to RELEASE_NOTES.md. The Release notes should be product specific - less technical details, more motivation and product consequences. Pay special attention to architectural decisions, make the list of the new proposed ADRs so the readers easily see the RFCs they can analyze and comment. 
3. For RNs make git diff <prev_version> <new_version> to see the difference between two releases without the intermediary experiments. when you write the RNs these experiments should disappear if they are not in this diff between two releases. the readers are not in the context of the process, they need the result. You need the snapshot of the real changes result, not the process in the changelog. These are two different tasks for changelog and for release notes. This is important.
3. update README.md file to reflect the actual repo information and What's new section based on the changelog and release notes you have updated. Keep only three last updates including the current one. 
4. write a telegram post on the new update, see misc/pr/tg_channel_ai_learning.



1) Analyze diff1. 2) Write the release notes to RELEASE_NOTES.md using ai_system/4_orchestration/workflows/release_notes_generation/Release_Notes.tmpl. Create a name for this release based on main changes, see previous releases examples in RELEASE_NOTES.md. 3) Update README.md: a) What's new section, b) optionally, other parts, if needed. 4) Write a telegram post about a new release to misc/pr/tg_channel_ai_learning/, use other tg posts as an example for style and formatting.

/add diff1 misc/pr/tg_channel_ai_learning/ RELEASE_NOTES.md README.md ai_system/4_orchestration/workflows/release_notes_generation/Release_Notes.tmpl


/run release_notes_data.sh $(git describe --tags --abbrev=0) HEAD > diff1

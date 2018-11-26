# tiger-bball
The overall goal of this project is to improve Towson University’s Men’s Basketball team’s chances of winning games based on statistical analysis of game data. The basketball team has requested our research group to identify which parameters in a game most affect the outcome and to identify optimal lineup combinations. To approach the ultimate task, I am focusing on play-by-play data extraction and analysis. From play-by-play analysis, I plan to identify which parameters influence a game’s outcome and determine whether different parameters affect a game’s outcome when grouped together. The conversion from raw play-by-play data to a suitable data form will help both the coaching staff on the basketball team and fellow research team members to interact with the data more easily. Preliminary work has been completed for this project from June 2018 through August 2018 and will continue in January 2019.

For more information, including background, methodology, and future work, see the `project_details` directory and compile `tiger_bball_summary.tex` with XeLaTeX (Packages required: geometry, amsmath, amssymb, fancyhdr, frontspec, hyperref, caption, graphicx, enumitem).

# events.py
This part of the project was done in collaboration with my research advisor. As described in tiger_bball_summary, play-by-play data must be extracted in order to placed into a dataframe. `events.py` evaluates an HTML page and properly categorizes events on the order in which they occur. In this case, it reads the file `Delaware 67-65_for_TU.html` and locates where to begin data extraction. Once it has located the right region of the page, it categorizes events. The file `timestamps.html` shows a sample of how this file works. After the import command, the next two commands extract each row of the play-by-play data as elements of a list. The command after those two displays the timestamp of a certain event with its corresponding period of play. The next output is a list of all the occurences of a steal within a game. The final output is a list of all the players who committed a steal in a game.

This part of the project is currently a work in progress.

# Background
This project is done in collaboration with my research advisor, [Dr. Christopher Cornwell](https://tigerweb.towson.edu/ccornwell/). The overall goal of this project is to improve Towson University’s Men’s Basketball team’s chances of winning games based on statistical analysis of game data. The basketball team has requested our research group to identify which parameters in a game most affect the outcome and to identify optimal lineup combinations. To approach the ultimate task, I am focusing on play-by-play data extraction and analysis. To analyze the play-by-play data, I will be using the [DBSCAN clustering algorithm](https://towardsdatascience.com/how-dbscan-works-and-why-should-i-use-it-443b4a191c80) and applying topological analysis. From play-by-play analysis, I plan to identify which parameters influence a game’s outcome and determine whether different parameters affect a game’s outcome when grouped together. The conversion from raw play-by-play data to a suitable data form will help both the coaching staff on the basketball team and fellow research team members to interact with the data more easily. Play-by-play data extraction has been completed for this project from June 2018 through May 2019; play-by-play data analysis will continue in August 2019.

This project was one of only four nominated to represent Towson University in the 2019 [Barry Goldwater Scholarship](https://goldwater.scholarsapply.org/), a highly selective scholarship awared to sophomore and junior STEM students who intend to develop into research leaders in STEM. To view the report submitted to the Goldwater Scholarship Foundation, which includes background, methodology, and future work, see `project_details` and compile `tiger_bball_summary.tex` with XeLaTeX (Packages required: geometry, amsmath, amssymb, fancyhdr, fontspec, hyperref, caption, graphicx, enumitem).

# Play-By-Play Data Extraction
To analyze the play-by-play data, all data from the team's statistics pages must be extracted. `events.py` evaluates an HTML page and categorizes events based on when they occur. An example of a webpage we are working with can be found [here](https://static.towsontigers.com/custompages/MBB/17-18/mb021518.htm). Unfortunately, data in some seasons are formatted differently. The figures below show the difference in formatting of statistics in different seasons:


<img src="/project_details/pbp_2013.png"> <img src="/project_details/pbp_2017.png">

Statistics from the 2013-2014 season (top figure) are placed in HTML-formatted tables, which makes data extraction relatively easy. Conversely, statistics from the 2017-2018 season (bottom figure) are in text-formatted tables, which makes data extraction difficult. Code for data extraction of the latter, more difficult format is complete (this is what is in `events.py`). Once all play-by-play data is retrieved, the data is placed into a dataframe.

Each dataframe corresponds to a single game and consists of the time at which a play occurs, the order in which a series of events occur, the players associated with each event, and the points scored in each play. The figure below shows an example of a single play.

<img src="/images/event_dict.png" width="900">

Using [a paper](https://statsbylopez.files.wordpress.com/2016/01/jqas-2007-3-3-1070.pdf) that identifies important factors in a basketball game (referred to as "The Four Factors"), we can obtain these factors for each player to implement our analysis. This requires us to perform computations based on the extracted data, such as turnovers per possession, effective field goal percentage, and offensive rebound percentage. Below is an example of a player's factors:

**Image coming soon!**

A numpy array for a player can be generated for any time interval. The elements in the numpy array are in the following order: field goals attempted, effective field goal percentage, turnovers per possession, offensive rebound percentage, number of fouls, and effective free throw percentage.

# Future work: Clustering Algorithm and Topological Analysis
Once all play-by-play data have been placed into a dataframe, a clustering algorithm and topology will be applied to the factors mentioned above. The clustering algorithm we will be using is DBSCAN, an algorithm that groups data based on areas of high and low density. Once the clustering is completed, [topological techniques](https://www.ams.org/journals/bull/2009-46-02/S0273-0979-09-01249-X/) introduced by Dr. Gunnar Carlsson will be applied to understand which parameters have the greatest influence when grouped together. This is done with the understanding that there is not just one type of grouping of parameters. Topological data analysis highlighed by Carlsson will enable extraction of those types.

Our planned topological analysis is based on [a study](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4780757/) conducted on the discovery of subgroups of Type 2 (T2) diabetes. In this study, researchers used a topological approach to construct a model to characterize the complexity of T2 diabetes patient populations based on electronic medical records and genotype data. This study found strong similarities among different subgroups of T2 diabetes from high-dimensional relationships that could not be observed by hand, such as laboratory tests. Once patients were distinguished into subgroups, statistical methods were applied to clarify treatment options and sources of the disease for each subgroup. Ultimately, three subgroups fo T2 diabetes were found using the model, suggesting that more than two types of diabetes exist. Below are the networks generated from the study. The left image is a patient-patient network for 2,551 T2 diabetes patients; the right image is a genotype-phenotype network for three subgroups of T2 diabetes, which are indicated by different colors.

<img src="/images/t2_diabetes_crop.jpg" width="400"> <img src="/images/nihms760576f2.jpg" width="400">

Similar to the diabetes study, we want to find relationships from high-dimensional data. Each player generates a myriad of statistics each game and our goal is to identify which statistics are the most important. We do not want to consider the team's highest scoring players as a single type and place them in the same lineup at all times. Instead, topological analyis will allow us to identify statistics that have a major impact, including those that seem insignificant to a game's outcome. For example, the analysis will demonstrate if there is a similarity between one player's rebounding ability and another player's shooting ability. If there is a similarity, then we can construct a lineup consisting of those two players. Finding these similarities will optimize the team's chances of winning games.

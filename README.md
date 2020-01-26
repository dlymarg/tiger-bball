# Background
This project is done in collaboration with my research advisor, [Dr. Christopher Cornwell](https://wp.towson.edu/ccornwell/). The overall goal of this project is to improve Towson University’s Men’s Basketball team’s chances of winning games based on statistical analysis of game data. The basketball team has requested our research group to identify which parameters in a game most affect the outcome and to identify optimal lineup combinations. To approach the ultimate task, I am focusing on play-by-play data extraction and analysis. To analyze the play-by-play data, I use the [Mapper algorithm](https://research.math.osu.edu/tgda/mapperPBG.pdf). From play-by-play analysis, I plan to identify which parameters influence a game’s outcome and determine whether different parameters affect a game’s outcome when grouped together. Furthermore, I plan to determine optimal lineup combinations in given game scenarios. The conversion from raw play-by-play data to a suitable data form will help both the coaching staff on the basketball team and fellow research team members to interact with the data more easily.

Our analysis is based on [a study](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4780757/) conducted on the discovery of subgroups of Type 2 (T2) diabetes. In this study, researchers used a topological approach to construct a model to characterize the complexity of T2 diabetes patient populations based on electronic medical records and genotype data. This study found strong similarities among different subgroups of T2 diabetes from high-dimensional relationships that could not be observed by hand, such as laboratory tests. Once patients were distinguished into subgroups, statistical methods were applied to clarify treatment options and sources of the disease for each subgroup. Ultimately, three subgroups fo T2 diabetes were found using the model, suggesting that more than two types of diabetes exist. Below are the networks generated from the study. The left image is a patient-patient network for 2,551 T2 diabetes patients; the right image is a genotype-phenotype network for three subgroups of T2 diabetes, which are indicated by different colors.

<img src="/images/t2_diabetes_crop.jpg" width="400"> <img src="/images/nihms760576f2.jpg" width="400">

Similar to the diabetes study, we want to find relationships from high-dimensional data. Each player generates a myriad of statistics each game and our goal is to identify which statistics are the most important. We do not want to consider the team's highest scoring players as a single type and place them in the same lineup at all times. Instead, topological analyis will allow us to identify statistics that have a major impact, including those that seem insignificant to a game's outcome. For example, the analysis will demonstrate if there is a similarity between one player's rebounding ability and another player's shooting ability. If there is a similarity, then we can construct a lineup consisting of those two players. Finding these similarities will optimize the team's chances of winning games.


This project was one of only 4 nominated to represent Towson University in the 2019 [Barry Goldwater Scholarship](https://goldwater.scholarsapply.org/), a highly selective scholarship awared to sophomore and junior STEM students who intend to develop into research leaders in STEM. To view the report submitted to the Goldwater Scholarship Foundation, which includes background, methodology, and future work, see `project_details` and compile `tiger_bball_summary.tex` with XeLaTeX (Packages required: geometry, amsmath, amssymb, fancyhdr, fontspec, hyperref, caption, graphicx, enumitem).

# Play-By-Play Data Extraction
To analyze the play-by-play data, all data from the team's statistics pages must be extracted. `events12.py` evaluates an HTML page and categorizes events based on when they occur. An example of a webpage we are working with can be found [here](https://static.towsontigers.com/custompages/MBB/17-18/mb021518.htm). Once all play-by-play data is retrieved, the data is placed into a dataframe.

Each dataframe corresponds to a single game and consists of the time at which a play occurs, the order in which a series of events occur, the players associated with each event, and the points scored in each play. The figure below shows an example of a single play. In this example, the user input is the timestamp representing 5 minutes and 24 seconds remaining in the first half. Notice that the primary event is a good layup by Gorham, the secondary event is a foul committed by Gustys, and the tertiary event is a good free throw shot by Gorham. During this play, Towson scored 3 points and two players on each team were substituted. The "1" next to a player's name shows that they are on the court during this play.

<img src="/images/event_dict.png" width="900">

After storing all play-by-play data in a dictionary, we can perform calculations on the dataset. Some examples of calculations we can perform are in the file `examples.v1.ipynb`. For the purposes of our analysis, we quantify the data using statistician Dean Oliver's [Four Factors](https://statsbylopez.files.wordpress.com/2016/01/jqas-2007-3-3-1070.pdf), which identifies important factors in a basketball game. We generate Four Factors statistics for each player (a Four Factors _profile_) to implement our analysis. This requires us to perform computations based on the extracted data, such as effective field goal percentage, turnovers per possession, and offensive rebound percentage. These computations are calculated for each on-court player over a selected 10-minute interval. The time intervals we use for each half are (in MM:SS format) 20:00-10:00, 15:00-05:00, and 10:00-00:00. We also compute a variation of the plus/minus statistic, which takes the difference of the points Towson scores from the points Towson's opponent scores over the selected time interval (e.g., if Towson scores 10 points and their opponent scores 7 points over a 10-minute interval, the plus/minus statistic over this interval would yield 3 points). The implementation of the Four Factors and plus/minus statistic are discussed in the next section (on data visualization).

Every Four Factors profile is stored in a numpy array. The elements in the numpy array are in the following order: field goals attempted, effective field goal percentage, turnovers per possession, offensive rebound percentage, number of fouls, and effective free throw percentage.

# Visualization of Play-By-Play Data Using the Mapper Algorithm

We use a network of nodes and edges (i.e., a _graph_) to visualize our dataset by using the Mapper algorithm. Our data points consist of the Four Factors profiles generated for each on-court player under the time intervals mentioned above. The plus/minus statistic that is calculated with each time interval is associated to each data point. Data points with similar Four Factors statistics are considered as part of the same node. Similar data points are grouped by the [DBSCAN algorithm](https://towardsdatascience.com/how-dbscan-works-and-why-should-i-use-it-443b4a191c80). A metric is used to add in edges as Four Factors statistics vary and as one traverses along the graph, the variation of the plus/minus statistic (mentioned above) is used. The goal of data visualization is the identify Four Factors profiles that consistently appear for each on-court player and in conjuction with a very positive or a very negative plus/minus statistic. Such knowledge may be useful to identify optimal lineup combinations at key points in games. Below is the output from the Mapper algorithm for the 2017-8 season

<img src="/images/mapper_graph.png">

An interactive version of our mapper graph is available in `basketball_mapper.html`. It is very likely that the arrangements of components will differ from the image, but the graphs are the same. As you hover your mouse over the nodes in each graph, you will see the Four Factors profiles in each node.

<!-- Future work: Clustering Algorithm and Topological Analysis -->
<!-- Once all play-by-play data have been placed into a dataframe, a clustering algorithm and topology will be applied to the factors mentioned above. The clustering algorithm we will be using is DBSCAN, an algorithm that groups data based on areas of high and low density. Once the clustering is completed, [topological techniques](https://www.ams.org/journals/bull/2009-46-02/S0273-0979-09-01249-X/) introduced by Dr. Gunnar Carlsson will be applied to understand which parameters have the greatest influence when grouped together. This is done with the understanding that there is not just one type of grouping of parameters. Topological data analysis highlighed by Carlsson will enable extraction of those types. -->

# Preliminary Results

Note that each node in the graph above is associated with a color. Moreover, each component of the graph has a transition of colors, from purple to yellow. For our project, each color is associated with the variation of the plus/minus statistic mentioned in the play-by-play data extraction section. Our goal is to understand which Four Factors profiles consistent appear on the court and in conjunction with a very negative plus/minus statistic or a very positive plus/minus statistic. We also want to understand what distinguishes components: how is the trend in plus/minus statistic in component A different from the trend in plus/minus statistic in component B? If we observe the series of nodes in the bottom right component from the darkest purple node to the last node before the fork, we get the following trends:

<img src="/images/long_arm_fgp.pdf" width="200">
<img src="/images/long_arm_to.pdf" width="200">
<img src="/images/long_arm_oreb.pdf" width="200">
<img src="/images/long_arm_ftr.pdf" width="200">

It is clear that this component corresponds to more efficient field goal shooting and fewer turnovers per possession. These trends also agree with what one would think would contribute to better scoring. However, these trends are not as clear in other components. In the middle/top component, we observe the series of nodes that run from the middle of the image to the "middle" point in the component:

<img src="/images/dark_tri_arm_fgp.pdf" width="200">
<img src="/images/dark_tri_arm_to.pdf" width="200">
<img src="/images/dark_tri_arm_oreb.pdf" width="200">
<img src="/images/dark_tri_arm_ftr.pdf" width="200">

We will need to implement different analysis techniques to better understand the nature of the latter series of nodes.

# Future Work: More Expansive Data Extraction and Analysis

Unfortunately, data in some seasons are formatted differently. The figures below show the difference in formatting of statistics in different seasons:

<img src="/project_details/pbp_2013.png"> <img src="/project_details/pbp_2017.png">

Statistics from the 2013-2014 season (top figure) are placed in HTML-formatted tables, which makes data extraction relatively easy. Conversely, statistics from the 2017-2018 season (bottom figure) are in text-formatted tables, which makes data extraction difficult. Code for data extraction of the latter, more difficult format is complete (this is what is in `events12.py`). In the future, we hope to extract and implmement analysis on play-by-play data from other seasons.

One avenue we can consider in our analysis is altering different parameters. For example, our analysis could change if we analyzed trends of Four Factors statistics in groups rather than individually. Additionally, we can potentially place different weights---or levels of importance---on different Four Factors statistics. In [the paper](https://statsbylopez.files.wordpress.com/2016/01/jqas-2007-3-3-1070.pdf) that outlines the Four Factors, field goal efficiency has the greatest weight, while free throw rate has the least weight. In other words, a team's field goal percentage is the greatest indicator (among the Four Factors statistics) of how a team will perform in a game. Finally, we can also adjust the length of time intervals in the Four Factors profiles. Since college basketball games are composed of two 20-minute halves, 10-minute time intervals divide each half of the game nicely.

Another avenue we can consider is applying multivariate linear regression on our graph. This would make the process of analyzing trends of nodes in our graph quicker than analyzing trends of nodes using univariate linear regression (displayed above)

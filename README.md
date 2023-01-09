# EHB328_TermProject_Embed2Detect
Forked from https://github.com/HHansi/Embed2Detect for my EHB 328 Term Project at Istanbul Tech Uni

I am taking the course 'EHB-328' at Istanbul Technical University. For our term project we are expected to pick an academic research project, run its codes and demonstrate how it works. For this I picked 'Embed2Detect'. The article by Hettiarachchi, H., Adedoyin-Olowe, M., Bhogal, J. et al. can be found at this link:
https://rdcu.be/cXTKq

Because I used a newer version of the Gensim package I had to change some code in "main.py" and "word_embedding_util.py". The only big change I made was using the KeyedVectors method from the Gensim libraries instead of the now-removed ".vocab" attributes.

I used Twint to produce a dataset myself, as I didn't have access to the Twitter Developer API.

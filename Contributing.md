# How to contribute

I'm really glad you're reading this, because Nuclei needs diversity and exelence inorder to become the great software I know it can be.

Here are some important resources:

* [Flask Tutorials](https://realpython.com/tutorials/flask/) I reccomend this website,
* [Our roadmap](https://imgur.com/sT2Nty5) is the near future aspriations for Nuclei, and
* [Discord](https://discord.gg/Ss6Tu4BD). Core Contributors will usually answer questions out of thier own volition, otherwise other users will be available for help.

## Submitting changes

Please send a [GitHub Pull Request to Nuclei](https://github.com/Wizock/Nuclei/pulls) with a clear list of what you've done (read more about [pull requests](http://help.github.com/pull-requests/)). When you send a pull request, we will love you forever if you include RSpec examples. We can always use more test coverage. Please follow our coding conventions (below) and make sure all of your commits are atomic (one feature per commit).
Assure no meta data or trashfiles arent being commited. GitIgnore will handle most of the pollution, however, assure you're not anyways.
Always write a clear log message for your commits. One-line messages are fine for small changes, but bigger changes should look like this:

```cmd
    $ git commit -m "A brief summary of the commit
    > 
    > A paragraph describing what changed and its impact."
```

## Coding conventions

Start reading our code and you'll get the hang of it. We optimize for readability and latest conventions to support and accommodate PEPs:

* We indent using Tabs (no spaces please)
* We use Black Formatter where ever necessary (please ensure your code is formatted)
* View files need to be deviated from the logic which is being applied from data requested
  * if a view is handling data, design seperate scoped functions/classes to handle data
  * Python and fastapi operations are seperated to maximise readability and debuggability
  * avoid cluttering view routes with exceptions
* Current File Structure is concrete and wont be facing changes anytime soon
* Tests arent nessisary, however, if written and failed, pull request will be denied
* Perfect pull requests arent a requirement, logic improvements are always appreciated
* Assure code follows PEP8 rulesets, however to iterate again, its not an requirement, the requirement is to format the python code.

Thanks,
Rohaan Ahmed, Core Developer - Nuclei

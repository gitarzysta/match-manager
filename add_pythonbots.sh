#!/bin/bash
for bot in bots/*
do
  if [ -d $bot ]
  then
    botname=${bot/bots\//}
    ./manager.py -A $botname -p "python3 $bot/MyBot.py"
  fi
done

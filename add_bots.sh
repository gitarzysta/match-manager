#!/bin/bash
for bot in bots/*
do
  if [ -f $bot ]
  then
    botname=${bot/bots\//}
    ./manager.py -A $botname -p $bot
  fi
done

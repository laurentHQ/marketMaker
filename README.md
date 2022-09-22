Access okcoin's digital currency quotes and make market making on the ZhongAn exchange

Author: Wu Dian (Andy.Woo) @Shanghai Mobile/WeChat: 18621528717

Project Introduction
One. Code structure

1.api

Access the tick quotes of digital currency on the okcoin counter from okcoin through the websocket protocol, and read and write the quotes of digital currency from the ZhongAn exchange through the rest protocol

2.dataRecorder

Based on the API interface, the tick of the digital currency obtained by okcoin is converted into a custom structure and stored in the mongoDB database in real time

3. Gateway

Convert externally acquired market structures into custom structures

4.strategy

Contains custom data structures within the system flow process and market maker strategy

4.1. MMBase defines data structures such as tick and bar

4.2.MMEngine implements the CTA policy engine, which abstracts and simplifies the functions of some of the underlying interfaces for CTA type policies

4.3. MMTemplate contains templates for policy development in the CTA engine, and the CtaTemplate class needs to be inherited when developing policies

4.4. MMStrategy Market Maker Strategy (see doc/Market Maker Strategy .txt for details)

4.5.vtMMClient Main Engine and Program Entry

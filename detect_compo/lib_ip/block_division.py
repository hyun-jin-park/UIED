import cv2
import numpy as np
from random import randint as rint
import time

import lib_ip.ip_preprocessing as pre
import lib_ip.ip_detection_utils as util
import lib_ip.ip_detection as det
import lib_ip.ip_draw as draw
import lib_ip.ip_segment as seg
from lib_ip.Block import Block
from config.CONFIG_UIED import Config
C = Config()


def block_hierarchy(blocks):
    for i in range(len(blocks) - 1):
        for j in range(i + 1, len(blocks)):
            relation = blocks[i].compo_relation(blocks[j])
            if relation == -1:
                blocks[j].children.append(i)
            if relation == 1:
                blocks[i].children.append(j)
    return


def block_bin_erase_all_blk(binary, blocks, pad=0, show=False):
    '''
    erase the block parts from the binary map
    :param binary: binary map of original image
    :param blocks_corner: corners of detected layout block
    :param show: show or not
    :param pad: expand the bounding boxes of blocks
    :return: binary map without block parts
    '''

    bin_org = binary.copy()
    for block in blocks:
        block.block_erase_from_bin(binary, pad)
    if show:
        cv2.imshow('before', bin_org)
        cv2.imshow('after', binary)
        cv2.waitKey()
    return binary


def block_division(grey, show=False, write_path=None,
                   grad_thresh=C.THRESHOLD_BLOCK_GRADIENT,
                   line_thickness=C.THRESHOLD_LINE_THICKNESS,
                   min_rec_evenness=C.THRESHOLD_REC_MIN_EVENNESS,
                   max_dent_ratio=C.THRESHOLD_REC_MAX_DENT_RATIO,
                   min_block_height_ratio=C.THRESHOLD_BLOCK_MIN_HEIGHT):
    '''
    :param grey: grey-scale of original image
    :return: corners: list of [(top_left, bottom_right)]
                        -> top_left: (column_min, row_min)
                        -> bottom_right: (column_max, row_max)
    '''
    blocks = []
    mask = np.zeros((grey.shape[0]+2, grey.shape[1]+2), dtype=np.uint8)
    broad = np.zeros((grey.shape[0], grey.shape[1], 3), dtype=np.uint8)

    row, column = grey.shape[0], grey.shape[1]
    for x in range(0, row, 10):
        for y in range(0, column, 10):
            if mask[x, y] == 0:
                # region = flood_fill_bfs(grey, x, y, mask)

                # flood fill algorithm to get background (layout block)
                mask_copy = mask.copy()
                cv2.floodFill(grey, mask, (y,x), None, grad_thresh, grad_thresh, cv2.FLOODFILL_MASK_ONLY)
                mask_copy = mask - mask_copy
                region = np.nonzero(mask_copy[1:-1, 1:-1])
                region = list(zip(region[0], region[1]))

                # ignore small regions
                if len(region) < 500:
                    continue
                block = Block(region)
                # get the boundary of this region
                # ignore lines
                if block.compo_is_line(line_thickness):
                    continue
                # ignore non-rectangle as blocks must be rectangular
                if not block.compo_is_rectangle(min_rec_evenness, max_dent_ratio):
                    continue
                if block.height/row < min_block_height_ratio:
                    continue
                blocks.append(block)
                draw.draw_region(region, broad)
    if show:
        cv2.imshow('block', broad)
        cv2.waitKey()
    if write_path is not None:
        cv2.imwrite(write_path, broad)
    return blocks

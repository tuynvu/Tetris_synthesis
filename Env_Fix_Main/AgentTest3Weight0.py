import copy
import numpy as np

################################################
#                  CONST VALUE                 #
################################################

TETRIS_SHAPES = [
    [[1, 1, 1, 1]],

    [[2, 2],
     [2, 2]],

    [[3, 0, 0],
     [3, 3, 3]],

    [[0, 0, 4],
     [4, 4, 4]],

    [[5, 5, 0],
     [0, 5, 5]],

    [[0, 6, 6, 6],
     [6, 6, 0, 0]],

    [[0, 7, 0],
     [7, 7, 7]],
]


################################################
#                   FUNCTION                   #
################################################
# rotate left
def rotate_clockwise(shape):
    return [[shape[y][x]
             for y in range(len(shape))]
            for x in range(len(shape[0]) - 1, -1, -1)]

################################################
#                      CLass                   #
################################################
class Field(object):
    def __init__(self, width, height, linesent):
        self.width = width
        self.height = height
        self.linesent = linesent
        self.field = [[0] * self.width] * self.height

    def size(self):
        return self.width, self.height

    def updateField(self, field):
        self.field = field

    @staticmethod
    def check_collision(field, shape, offset):
        off_x, off_y = offset
        for cy, row in enumerate(shape):
            for cx, cell in enumerate(row):
                try:
                    if cell and field[cy + off_y][cx + off_x]:
                        return True
                except IndexError:
                    return True
        return False

    def projectPieceDown(self, piece, offsetX, workingPieceIndex):
        if offsetX + len(piece[0]) > self.width or offsetX < 0:
            return None
        offsetY = self.height
        for y in range(0, self.height):
            if Field.check_collision(self.field, piece, (offsetX, y)):
                offsetY = y
                break
        for x in range(0, len(piece[0])):
            for y in range(0, len(piece)):
                value = piece[y][x]
                if value > 0:
                    self.field[offsetY - 1 + y][offsetX + x] = -workingPieceIndex
        return self

    def undo(self, workingPieceIndex):
        self.field = [[0 if el == -workingPieceIndex else el for el in row] for row in self.field]

    def heightForColumn(self, column):
        width, height = self.size()
        for i in range(0, height):
            if self.field[i][column] != 0:
                return height - i
        return 0

    def heights(self):
        result = []
        width, height = self.size()
        for i in range(0, width):
            result.append(self.heightForColumn(i))
        return result

    def numberOfHoleInColumn(self, column):
        result = 0
        maxHeight = self.heightForColumn(column)
        for height, line in enumerate(reversed(self.field)):
            if height > maxHeight: break
            if line[column] == 0 and height < maxHeight:
                result += 1
        return result

    def numberOfHoleInRow(self, line):
        result = 0
        for index, value in enumerate(self.field[self.height - 1 - line]):
            if value == 0 and self.heightForColumn(index) > line:
                result += 1
        return result

    # |----------------------------------------------|
    #                   HEURISTICS                   #
    # |----------------------------------------------|

    def heuristics(self):
        heights = self.heights()
        maxColumn = self.maxHeightColumns(heights)
        return heights + [self.aggregateHeight(heights)] + self.numberOfHoles(heights) + self.bumpinesses(heights) + [
            self.completLine(), self.maxPitDepth(heights), self.maxHeightColumns(heights),
            self.minHeightColumns(heights)]

    def aggregateHeight(self, heights):
        result = sum(heights)
        return result

    def completLine(self):
        result = 0
        width, height = self.size()
        for i in range(0, height- self.linesent):
            if 0 not in self.field[i]:
                result += 1

        #######################################################
        if result == 0: return 0.8
        elif result == 1: return 1
        elif result == 2: return 10
        elif result == 3: return 100

        return 1000
        ########################################################

    def bumpinesses(self, heights):
        result = []
        for i in range(0, len(heights) - 1):
            result.append(abs(heights[i] - heights[i + 1]))
        return result

    def numberOfHoles(self, heights):
        results = []
        width, height = self.size()
        for j in range(0, width):
            result = 0
            for i in range(0, height):
                if self.field[i][j] == 0 and height - i < heights[j]:
                    result += 1
            results.append(result)
        return results

    def maxHeightColumns(self, heights):
        return max(heights)

    def minHeightColumns(self, heights):
        return min(heights)

    def maximumHoleHeight(self, heights):
        if self.numberOfHole(heights) == 0:
            return 0
        else:
            maxHeight = 0
            for height, line in enumerate(reversed(self.field)):
                if sum(line) == 0: break
                if self.numberOfHoleInRow(height) > 0:
                    maxHeight = height
            return maxHeight

    def rowsWithHoles(self, maxColumn):
        result = 0
        for line in range(0, maxColumn):
            if self.numberOfHoleInRow(line) > 0:
                result += 1
        return result

    def maxPitDepth(self, heights):
        return max(heights) - min(heights)

    @staticmethod
    def __offsetPiece(piecePositions, offset):
        piece = copy.deepcopy(piecePositions)
        for pos in piece:
            pos[0] += offset[0]
            pos[1] += offset[1]

        return piece

    def __checkIfPieceFits(self, piecePositions):
        for x, y in piecePositions:
            if 0 <= x < self.width and 0 <= y < self.height:
                if self.field[y][x] >= 1:
                    return False
            else:
                return False
        return True

    def fitPiece(self, piecePositions, offset=None):
        if offset:
            piece = self.__offsetPiece(piecePositions, offset)
        else:
            piece = piecePositions

        field = copy.deepcopy(self.field)
        if self.__checkIfPieceFits(piece):
            for x, y in piece:
                field[y][x] = 1

            return field
        else:
            return None


class GetBest(object):

    @staticmethod
    def best(field, workingPieces, workingPieceIndex, weights, level, workingIdPieces):
        bestRotation = None
        bestOffset = None
        bestScore = None
        workingPieceIndex = copy.deepcopy(workingPieceIndex)
        workingPiece = workingPieces[workingPieceIndex]
        workingIdPiece = workingIdPieces[workingPieceIndex]
        shapesRotation = {0: 2, 1: 1, 2: 4, 3: 4, 4: 2, 5: 4, 6: 4}

        for rotation in range(0, shapesRotation[workingIdPiece]):
            for offset in range(0, field.width):
                result = field.projectPieceDown(workingPiece, offset, level)
                if not result is None:
                    score = None
                    if workingPieceIndex == len(workingPieces) - 1:
                        heuristics = field.heuristics()
                        score = sum([a * b for a, b in zip(heuristics, weights)])
                    else:
                        _, _, score = GetBest.best(field, workingPieces, workingPieceIndex + 1, weights, level + 1,
                                                   workingIdPieces)

                    if (bestScore is None) or (score > bestScore):
                        bestScore = score
                        bestOffset = offset
                        bestRotation = rotation
                field.undo(level)
            workingPiece = rotate_clockwise(workingPiece)

        return bestOffset, bestRotation, bestScore

    @staticmethod
    def choose(initialField, piece, next_piece, offsetX, weights, parent, idPieceCrr, idNextPiece, linesent):
        field = Field(len(initialField[0]), len(initialField), linesent)
        field.updateField(copy.deepcopy(initialField))
        offset, rotation, _ = GetBest.best(field, [piece, next_piece], 0, weights, 1, [idPieceCrr, idNextPiece])
        moves = []

        # ==============================================================================================================
        # Ipiece
        if idPieceCrr == 0:
            if rotation == 1:
                offsetX += 1
        # opiece
        elif idPieceCrr == 1:
            offsetX = 5
        # Jpiece
        elif idPieceCrr == 2:
            if rotation == 3:
                offsetX += 1
        # Lpiece
        elif idPieceCrr == 3:
            if rotation == 3:
                offsetX += 1
        # Zpiece
        elif idPieceCrr == 4:
            if rotation == 3:
                offsetX += 1
        # Spiece
        elif idPieceCrr == 5:
            if rotation == 3:
                offsetX += 1
        # Tpiece
        else:
            if rotation == 3:
                offsetX += 1
        # ==============================================================================================================

        offset = offset - offsetX
        for _ in range(0, rotation):
            moves.append(4)
        for _ in range(0, abs(offset)):
            if offset > 0:
                moves.append(5)
            else:
                moves.append(6)
        moves.append(2)
        parent.listAction.extend(moves)


################################################
#                     Agent                    #
################################################

class Agent(object):
    def __init__(self, turn):
        self.listAction = []
        # self.weight = [-2.503203450528113, -6.232148141856897, -4.889022639678535, -5.483191625315361,
        #                -5.621116241119032, -7.167988262189014, -3.787280013510496, -7.1433724740204925,
        #                -6.820522834607067, 4.156362964813036, -23.764795034066324, -17.36836019094467,
        #                -6.6518818320983035, 2.7040604325130286, -19.764237133686873, -6.405123768951559,
        #                -6.258423157239519, -9.104965785418177, -3.9580234761128787, -1.9310935590686635,
        #                -13.801667307038553, -4.762971682982187, 0.839292713552033, -2.9922313458582694,
        #                -6.75452824882575, -6.900109485346231, -3.3173538574836168, -3.86242852312692,
        #                -7.3743581151540045, -2.0437270423997727, 9.836725060604877, -8.114889750599733,
        #                -8.895551330060245, 3.256322916796323]
        self.weight = [-2.288377460517875, -6.426867472412552, -2.6676753558339046, -4.904800928701944, -6.654776582364347,
        -7.2494738303370285, -3.7814621420779093, -6.625602678836543, -6.851516641462909, 4.26082136286486, -22.705276139120116,
        -17.47270934926082, -6.837412478350752, 3.4406804539695255, -12.054260756128006, -4.548971255899007, -6.380582883899651,
        -8.992206953177792, -4.540584796382033, -2.1238428737671713, -13.352657197693985, -4.57690246117096, 1.0425812028737798,
        -2.948201261372145, -6.130581380460365, -6.889581112942637, -3.534175127525335, -4.351486961320134, -7.314959727220688,
        -1.6526954488942005, 9.830718133147535, -8.246422633591889, -9.14034708605627, 3.1195208020062557]

    def getPieceCurrent(self, ob):
        grid = np.array(np.array(ob).squeeze()[:20, :10], dtype="float32")
        cvt_TF = grid == 0.3
        cols_sum = cvt_TF.sum(axis=0)
        rows_sum = cvt_TF.sum(axis=1)
        if sum(cols_sum) == 0:
            return False, False, False
        x = list(cols_sum > 0)
        y = list(rows_sum > 0)
        x1, x2 = x.index(1), x.index(1) + sum(x)
        y1, y2 = y.index(1), y.index(1) + sum(y)
        # position start cell top - left: x1, y1
        gr = np.array(cvt_TF[y1:y2, x1:x2], dtype="int32")
        piece = tuple([tuple([x for x in rows]) for rows in gr])
        # return TETRIS_SHAPES[DIC_PIECE[piece]], x1, y1

    def getNextPiece(self, ob, id):
        return TETRIS_SHAPES[np.array(np.array(ob).squeeze()[:20, 10:17], dtype="float32")[id].argmax()]

    def getIdPiece(self, ob, id):
        return np.array(np.array(ob).squeeze()[:20, 10:17], dtype="float32")[id].argmax()

    def getSentline(self, ob):
        # return int(np.array(np.array(ob).squeeze()[7, 10], dtype="float16") * 100)
        return int(np.array(np.array(ob).squeeze()[7, 27], dtype="float16") * 100)

    def getGrid(self, ob):
        return np.array(np.array(ob).squeeze()[:20, :10], dtype="int32")

    def maxHeight(self, board):
        return np.argmin(np.sum(board, axis=1)[::-1])

    def get7(self, ob):
        return np.array(np.array(ob).squeeze()[:20, 10:17], dtype="float32")

    def choose_action(self, observation):
        if len(self.listAction) != 0:
            return self.listAction.pop(0)
        else:
            # initialField
            board = self.getGrid(copy.deepcopy(observation))
            linesent = self.getSentline(copy.deepcopy(observation))

            # dic:  idpiece : init x, { I, O, J, L, Z, S, T}
            xPiece = {0: 4, 1: 5, 2: 4, 3: 4, 4: 4, 5: 4, 6: 4}

            # get piece, id of crr, next
            crr_piece, idPieceCrr = self.getNextPiece(copy.deepcopy(observation), 6), self.getIdPiece(
                copy.deepcopy(observation), 6)
            next_piece, idNextPiece = self.getNextPiece(copy.deepcopy(observation), 1), self.getIdPiece(
                copy.deepcopy(observation), 1)

            # get self.listAction
            GetBest.choose(board, crr_piece, next_piece, xPiece[idPieceCrr], self.weight, self, idPieceCrr, idNextPiece, linesent)

            # return action
            return self.choose_action(observation)
